import warnings
from decimal import Decimal
from itertools import chain

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView, RedirectView, TemplateView, View
from django.views.generic.detail import (
    DetailView,
    SingleObjectMixin,
    SingleObjectTemplateResponseMixin,
)
from django.views.generic.edit import (
    DeleteView,
    FormView,
    ModelFormMixin,
    ProcessFormView,
)
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from next_url_mixin.mixin import NextUrlMixin
from openwisp_utils.mixins import MultiTenantMixin, SuperuserPermissionMixin, OrganizationDbAdminMixin

from .forms import BillingInfoForm, CreateOrderForm, PaymentForm, FakePaymentsForm
from .importer import import_name
from .signals import order_started
from .utils import get_currency
from .validators import plan_validation

from .models import (
    UserPlan,
    PlanPricing,
    Plan,
    Order,
    BillingInfo,
    Quota,
    Invoice,
    Payment,
)

class AccountActivationView(LoginRequiredMixin, MultiTenantMixin, TemplateView):
    template_name = "gmtisp_billing/plans/account_activation.html"

    def get_context_data(self, **kwargs):
        user_plan = self.request.user.userplan
        if user_plan.active or user_plan.is_expired():
            raise Http404()

        context = super().get_context_data(**kwargs)
        errors = user_plan.clean_activation()

        if errors["required_to_activate"]:
            context["SUCCESSFUL"] = False
        else:
            context["SUCCESSFUL"] = True
            messages.success(self.request, _("Your account is now active"))

        for error in errors["required_to_activate"]:
            messages.error(self.request, error)
        for error in errors["other"]:
            messages.warning(self.request, error)

        return context


class PlanTableMixin:
    def get_plan_table(self, plan_list):
        """
        This method return a list in following order:
        [
            ( Quota1, [ Plan1Quota1, Plan2Quota1, ... , PlanNQuota1] ),
            ( Quota2, [ Plan1Quota2, Plan2Quota2, ... , PlanNQuota2] ),
            ...
            ( QuotaM, [ Plan1QuotaM, Plan2QuotaM, ... , PlanNQuotaM] ),
        ]

        This can be very easily printed as an HTML table element with quotas by row.

        Quotas are calculated based on ``plan_list``. These are all available quotas that are
        used by given plans. If any ``Plan`` does not have any of ``PlanQuota`` then value ``None``
        will be propagated to the data structure.

        """

        # Retrieve all quotas that are used by any ``Plan`` in ``plan_list``
        quota_list = Quota.objects.filter(planquota__plan__in=plan_list).distinct()

        # Create random access dict that for every ``Plan`` map ``Quota`` -> ``PlanQuota``
        plan_quotas_dic = {plan: {pq.quota: pq for pq in plan.planquota_set.all()} for plan in plan_list}

        # Generate data structure described in method docstring, propagate ``None`` whenever
        # ``PlanQuota`` is not available for given ``Plan`` and ``Quota``
        return [(quota, [plan_quotas_dic[plan].get(quota) for plan in plan_list]) for quota in quota_list]


class PlanListView(MultiTenantMixin, ListView):
    template_name = "gmtisp_billing/plans/plan_list.html"
    model = Plan
    context_object_name = "plans"


class PlanTableViewBase(PlanTableMixin, ListView):
    template_name = "gmtisp_billing/plans/plan_table.html"
    model = Plan
    context_object_name = "plan_list"

    def get_queryset(self):
        queryset = (
            super().get_queryset()
            .prefetch_related("planpricing_set__pricing", "planquota_set__quota")
        )
        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(available=True, visible=True)
                & (Q(customized=self.request.user) | Q(customized__isnull=True))
            )
        else:
            queryset = queryset.filter(
                Q(available=True, visible=True) & Q(customized__isnull=True)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            try:
                self.userplan = UserPlan.objects.select_related("plan").get(
                    user=self.request.user
                )
            except UserPlan.DoesNotExist:
                self.userplan = None

            context["userplan"] = self.userplan

            try:
                context["current_userplan_index"] = list(self.object_list).index(
                    self.userplan.plan
                )
            except (ValueError, AttributeError):
                pass

        context["plan_table"] = self.get_plan_table(self.object_list)
        context["CURRENCY"] = settings.PLANS_CURRENCY

        return context


class CurrentPlanView(LoginRequiredMixin, MultiTenantMixin, PlanTableViewBase):
    template_name = "gmtisp_billing/plans/current.html"

    def get_queryset(self):
        return Plan.objects.filter(userplan__user=self.request.user).prefetch_related(
            "planpricing_set__pricing", "planquota_set__quota"
        )


class UpgradePlanView(LoginRequiredMixin, MultiTenantMixin, PlanTableViewBase):
    template_name = "gmtisp_billing/plans/upgrade.html"


class PricingView(LoginRequiredMixin, MultiTenantMixin, PlanTableViewBase):
    template_name = "gmtisp_billing/plans/pricing.html"


class ChangePlanView(LoginRequiredMixin, MultiTenantMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse("upgrade_plan"))

    def post(self, request, *args, **kwargs):
        plan = get_object_or_404(
            Plan,
            Q(pk=kwargs["pk"])
            & Q(available=True, visible=True)
            & (Q(customized=request.user) | Q(customized__isnull=True)),
        )
        if request.user.userplan.plan != plan:
            policy = import_name(
                getattr(
                    settings,
                    "PLANS_CHANGE_POLICY",
                    "gmtisp_billing.plan_change.StandardPlanChangePolicy",
                )
            )()

            period = request.user.userplan.days_left()
            price = policy.get_change_price(request.user.userplan.plan, plan, period)

            if price is None:
                request.user.userplan.extend_account(plan, None)
                messages.success(request, _("Your plan has been successfully changed"))
            else:
                return HttpResponseForbidden()
        return HttpResponseRedirect(reverse("upgrade_plan"))


class CreateOrderView(LoginRequiredMixin, MultiTenantMixin, CreateView):
    template_name = "gmtisp_billing/plans/create_order.html"
    form_class = CreateOrderForm

    def recalculate(self, amount, billing_info):
        order = Order(pk=-1)
        order.recalculate(amount, billing_info, self.request)
        return order

    def validate_plan(self, plan):
        validation_errors = plan_validation(self.request.user, plan)
        if validation_errors["required_to_activate"] or validation_errors["other"]:
            messages.error(
                self.request,
                _(
                    "The selected plan is insufficient for your account. "
                    "Your account will not be activated or will not work fully after completing this order."
                    "<br><br>Following limits will be exceeded: <ul><li>%(reasons)s</ul>"
                )
                % {
                    "reasons": "<li>".join(
                        chain(
                            validation_errors["required_to_activate"],
                            validation_errors["other"],
                        )
                    ),
                },
            )

    def get_all_context(self):
        self.plan_pricing = get_object_or_404(
            PlanPricing.objects.all().select_related("plan", "pricing"),
            Q(pk=self.kwargs["pk"])
            & Q(plan__available=True)
            & (
                Q(plan__customized=self.request.user) | Q(plan__customized__isnull=True)
            ),
        )

        if (
            not self.request.user.userplan.is_expired()
            and not self.request.user.userplan.plan.is_free()
            and self.request.user.userplan.plan != self.plan_pricing.plan
        ):
            raise Http404

        self.plan = self.plan_pricing.plan
        self.pricing = self.plan_pricing.pricing

    def get_billing_info(self):
        try:
            return self.request.user.billinginfo
        except BillingInfo.DoesNotExist:
            return None

    def get_price(self):
        return self.plan_pricing.price

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_all_context()
        context["billing_info"] = self.get_billing_info()

        order = self.recalculate(
            self.get_price() or Decimal("0.0"), context["billing_info"]
        )
        order.plan = self.plan_pricing.plan
        order.pricing = self.plan_pricing.pricing
        order.currency = get_currency()
        order.user = self.request.user
        context["object"] = order

        self.validate_plan(order.plan)
        return context

    def form_valid(self, form):
        self.get_all_context()
        order = self.recalculate(
            self.get_price() or Decimal("0.0"), self.get_billing_info()
        )

        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.plan = self.plan
        self.object.pricing = self.pricing
        self.object.amount = order.amount
        self.object.tax = order.tax
        self.object.currency = order.currency
        self.object.save()
        order_started.send(sender=self.object)
        return super().form_valid(form)


class CreateOrderPlanChangeView(CreateOrderView, LoginRequiredMixin, MultiTenantMixin):
    template_name = "gmtisp_billing/plans/create_order.html"
    form_class = CreateOrderForm

    def get_all_context(self):
        self.plan = get_object_or_404(
            Plan,
            Q(pk=self.kwargs["pk"])
            & Q(available=True, visible=True)
            & (Q(customized=self.request.user) | Q(customized__isnull=True)),
        )
        self.pricing = None

    def get_policy(self):
        policy_class = getattr(
            settings,
            "PLANS_CHANGE_POLICY",
            "gmtisp_billing.plan_change.StandardPlanChangePolicy",
        )
        return import_name(policy_class)()

    def get_price(self):
        policy = self.get_policy()
        userplan = self.request.user.userplan

        if userplan.expire is not None:
            period = self.request.user.userplan.days_left()
        else:
            period = 30

        return policy.get_change_price(
            self.request.user.userplan.plan, self.plan, period
        )

    def get_context_data(self, **kwargs):
        context = super(CreateOrderView, self).get_context_data(**kwargs)
        self.get_all_context()

        price = self.get_price()
        context["plan"] = self.plan
        context["billing_info"] = self.get_billing_info()
        if price is None:
            context["FREE_ORDER"] = True
            price = 0
        order = self.recalculate(price, context["billing_info"])
        order.pricing = None
        order.plan = self.plan
        order.user = self.request.user
        context["billing_info"] = context["billing_info"]
        context["object"] = order
        self.validate_plan(order.plan)
        return context


class OrderView(LoginRequiredMixin, MultiTenantMixin, DetailView):
    model = Order

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(user=self.request.user)
            .select_related("plan", "pricing")
        )


class OrderListView(LoginRequiredMixin, MultiTenantMixin, ListView):
    template_name = "gmtisp_billing/plans/order_list.html"
    model = Order
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.CURRENCY = getattr(settings, "PLANS_CURRENCY", None)
        if len(self.CURRENCY) != 3:
            raise ImproperlyConfigured(
                "PLANS_CURRENCY should be configured as 3-letter currency code."
            )
        context["CURRENCY"] = self.CURRENCY
        return context

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(user=self.request.user)
            .select_related("plan", "pricing")
        )


class OrderPaymentReturnView(LoginRequiredMixin, MultiTenantMixin, DetailView):
    model = Order
    status = None

    def render_to_response(self, context, **response_kwargs):
        if self.status == "success":
            messages.success(
                self.request,
                _(
                    "Thank you for placing a payment. It will be processed as soon as possible."
                ),
            )
        elif self.status == "failure":
            messages.error(
                self.request,
                _(
                    "Payment was not completed correctly. Please repeat payment process."
                ),
            )

        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(user=self.request.user)
        )


class SuccessUrlMixin:
    def get_success_url(self):
        messages.success(self.request, _("Billing info has been updated successfully."))
        return reverse("billing_info")


class CreateOrUpdateView(
    SingleObjectTemplateResponseMixin, ModelFormMixin, MultiTenantMixin, ProcessFormView
):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)


class BillingInfoCreateOrUpdateView(
    NextUrlMixin, SuccessUrlMixin, LoginRequiredMixin, CreateOrUpdateView
):
    form_class = BillingInfoForm
    template_name = "gmtisp_billing/plans/billing_info_create_or_update.html"

    def get_object(self):
        try:
            return self.request.user.billinginfo
        except (AttributeError, BillingInfo.DoesNotExist):
            return None

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(request=self.request)
        return kwargs


class RedirectToBilling(RedirectView):
    url = reverse_lazy("billing_info")
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        warnings.warn(
            "This view URL is deprecated. Use plain billing_info instead.",
            DeprecationWarning,
        )
        return super().get_redirect_url(*args, **kwargs)


class BillingInfoDeleteView(LoginRequiredMixin, MultiTenantMixin, DeleteView):
    template_name = "gmtisp_billing/plans/billing_info_delete.html"

    def get_object(self):
        try:
            return self.request.user.billinginfo
        except BillingInfo.DoesNotExist:
            raise Http404

    def get_success_url(self):
        messages.success(self.request, _("Billing info has been deleted."))
        return reverse("billing_info")


class InvoiceDetailView(LoginRequiredMixin, MultiTenantMixin, DetailView):
    model = Invoice

    def get_template_names(self):
        return getattr(settings, "PLANS_INVOICE_TEMPLATE", "gmtisp_billing/plans/invoices/PL_EN.html")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["logo_url"] = getattr(settings, "PLANS_INVOICE_LOGO_URL", None)
        context["auto_print"] = True
        return context

    def get_queryset(self):
        if self.request.user.is_superuser:
            return super().get_queryset().select_related("order")
        else:
            return (
                super().get_queryset()
                .filter(user=self.request.user)
                .select_related("order")
            )


class FakePaymentsView(LoginRequiredMixin, MultiTenantMixin, SingleObjectMixin, FormView):
    form_class = FakePaymentsForm
    model = Order
    template_name = "gmtisp_billing/payment/fake_payments.html"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_queryset(self):
        return (
            super().get_queryset().filter(user=self.request.user)
        )

    def dispatch(self, *args, **kwargs):
        if not getattr(settings, "DEBUG", False):
            return HttpResponseForbidden("This view is accessible only in debug mode.")
        self.object = self.get_object()
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        if int(form["status"].value()) == Order.STATUS.COMPLETED:
            self.object.complete_order()
            return HttpResponseRedirect(
                reverse("order_payment_success", kwargs={"pk": self.object.pk})
            )
        else:
            self.object.status = form["status"].value()
            self.object.save()
            return HttpResponseRedirect(
                reverse("order_payment_failure", kwargs={"pk": self.object.pk})
            )


# ----------------------------------------------------------- payment
class PaymentListView(LoginRequiredMixin, MultiTenantMixin, ListView):
    template_name = "gmtisp_billing/payments/payment_list.html"
    model = Payment
    context_object_name = "payments"

    def get_queryset(self):
        return super().get_queryset().filter(order__user=self.request.user)

class PaymentDetailView(LoginRequiredMixin, MultiTenantMixin, DetailView):
    template_name = "gmtisp_billing/payments/payment_detail.html"
    model = Payment
    context_object_name = "payment"

    def get_queryset(self):
        return super().get_queryset().filter(order__user=self.request.user)

class PaymentCreateView(LoginRequiredMixin, MultiTenantMixin, SuperuserPermissionMixin, CreateView):
    template_name = "gmtisp_billing/payments/payment_form.html"
    form_class = PaymentForm
    success_url = reverse_lazy("payment_list")

    def form_valid(self, form):
        messages.success(self.request, _("Payment created successfully."))
        return super().form_valid(form)

class PaymentUpdateView(LoginRequiredMixin, MultiTenantMixin, SuperuserPermissionMixin, UpdateView):
    template_name = "gmtisp_billing/payments/payment_form.html"
    form_class = PaymentForm
    model = Payment

    def get_success_url(self):
        return reverse_lazy("payment_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, _("Payment updated successfully."))
        return super().form_valid(form)

class PaymentDeleteView(LoginRequiredMixin, MultiTenantMixin, SuperuserPermissionMixin, DeleteView):
    model = Payment
    template_name = "gmtisp_billing/payments/payment_confirm_delete.html"
    success_url = reverse_lazy("payment_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _("Payment deleted successfully."))
        return super().delete(request, *args, **kwargs)














# class PaymentDetailView(LoginRequiredMixin, MultiTenantMixin, View):
#     login_url = reverse_lazy("auth_login")
#     template_name = "gmtisp_billing/payment.html"

#     def get(self, request, *args, payment_id=None):
#         payment = get_object_or_404(
#             get_payment_model(), order__user=request.user, id=payment_id
#         )
#         try:
#             form = payment.get_form(data=request.POST or None)
#         except RedirectNeeded as redirect_to:
#             payment.save()
#             return redirect(str(redirect_to))
#         return TemplateResponse(
#             request, "gmtisp_billing/payment.html", {"form": form, "payment": payment}
#         )


# def get_client_ip(request):
#     return request.META.get("REMOTE_ADDR")


# def create_payment_object(
#     payment_variant, order, request=None, autorenewed_payment=False
# ):
#     Payment = get_payment_model()
#     if (
#         hasattr(order.user.userplan, "recurring")
#         and order.user.userplan.recurring.payment_provider != payment_variant
#     ):
#         order.user.userplan.recurring.delete()
#     return Payment.objects.create(
#         variant=payment_variant,
#         order=order,
#         description=f"{order.name} purchase",
#         total=Decimal(order.total()),
#         tax=Decimal(order.tax_total()),
#         currency=order.currency,
#         delivery=Decimal(0),
#         billing_first_name=order.user.first_name,
#         billing_last_name=order.user.last_name,
#         billing_email=order.user.email or "",
#         billing_address_1=order.user.billinginfo.street,
#         # billing_address_2=order.user.billinginfo.zipcode,
#         billing_city=order.user.billinginfo.city,
#         billing_postcode=order.user.billinginfo.zipcode,
#         billing_country_code=order.user.billinginfo.country,
#         # billing_country_area=order.user.billinginfo.zipcode,
#         customer_ip_address=get_client_ip(request) if request else "127.0.0.1",
#         autorenewed_payment=autorenewed_payment,
#     )


# class CreatePaymentView(LoginRequiredMixin, MultiTenantMixin, View):
#     login_url = reverse_lazy("auth_login")

#     def get(self, request, *args, order_id=None, payment_variant=None):
#         order = get_object_or_404(Order, pk=order_id, user=request.user)
#         payment = create_payment_object(payment_variant, order, request)
#         return redirect(reverse("payment_details", kwargs={"payment_id": payment.id}))