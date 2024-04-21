import json
import logging
from decimal import Decimal
from urllib.parse import urljoin

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.dispatch.dispatcher import receiver
from django.urls import reverse

from openwisp_users.mixins import OrgMixin

from swapper import swappable_setting

from plans.base.models import (
    AbstractBillingInfo,
    AbstractInvoice,
    AbstractOrder,
    AbstractPlan,
    AbstractPlanPricing,
    AbstractPlanQuota,
    AbstractPricing,
    AbstractQuota,
    AbstractRecurringUserPlan,
    AbstractUserPlan,
)

from payments import PaymentStatus, PurchasedItem
from payments.core import get_base_url
from payments.models import BasePayment
from payments.signals import status_changed

from .contrib import get_user_language, send_template_email
from .signals import account_automatic_renewal
# from .views import create_payment_object

logger = logging.getLogger(__name__)



class Plan(OrgMixin, AbstractPlan):
    # Test existing fields can be modified
    default = models.BooleanField(
        help_text=AbstractPlan._meta.get_field("default").help_text,
        default=AbstractPlan._meta.get_field("default").default,
        null=True,
        blank=True,
    )

    """
    The base plan object

    There's three kinds of plans; they're distinguished by the structure
    field.

    - A stand alone plan. Regular plan that lives by itself.
    - A child plan. All child plans have a parent plan. They're a
      specific version of the parent.
    - A parent plan. It essentially represents a set of plans.

    An example could be a yoga course, which is a parent plan. The different
    times/locations of the courses would be associated with the child plans.
    """

    STANDALONE, PARENT, CHILD = 'standalone', 'parent', 'child'
    STRUCTURE_CHOICES = (
        (STANDALONE, _('Stand-alone plan')),
        (PARENT, _('Parent plan')),
        (CHILD, _('Child plan'))
    )
    structure = models.CharField(_("Plan structure"), max_length=16,
        choices=STRUCTURE_CHOICES, default=STANDALONE
        )

    parent = models.ForeignKey('self', on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='children',
        verbose_name=_("Parent plan"),
        help_text=_("Only choose a parent plan if you're creating a child "
                    "plan.  For example if this is a size "
                    "4 of a particular t-shirt.  Leave blank if this is a "
                    "stand-alone plan (i.e. there is only one version of"
                    " this plan).")
        )

    BANDWIDTH, DATA = 'Bandwidth', 'Data'
    plan_class_choices = (
        (BANDWIDTH, _('Bandwidth')),
        (DATA, _('Data')),
    )
    plan_class = models.CharField(_("Plan Class"), max_length=16, default=DATA, choices=plan_class_choices) 

    PREPAID, POSTPAID = 'Prepaid', 'Postpaid'
    plan_type_choices = (
        (PREPAID, _('Prepaid')),
        (POSTPAID, _('Postpaid')),
    )
    type_of = models.CharField(_("Plan Type"), max_length=16, default=PREPAID, choices=plan_type_choices)

    recrurring = models.BooleanField(_("Plan Recrurring"), 
        default=True, 
        help_text=_( "This flag indicates if this plan is recrurring")
        )    
    
    DAILY, WEEKLY, MONTHLY, QUARTERLY, SEMIYEARLY, YEARLY, NOEXPIRY = 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Semi-Yearly', 'Yearly', 'No Expiry'
    recurring_period_choices = (
        (DAILY, _('Daily')),
        (WEEKLY, _('Weekly')),
        (MONTHLY, _('Monthly')),
        (QUARTERLY, _('Quarterly')),
        (SEMIYEARLY, _('Semi-Yearly')),
        (YEARLY, _('Yearly')),
        (NOEXPIRY, _('No Expiry')),
    )
    recrurring_period = models.CharField(_("Plan Recrurring Period"), max_length=16, default=MONTHLY, 
        choices=recurring_period_choices
        )
    
    FIXED, ANNIVERSARY = 'Fixed', 'Anniversary'
    schedule_choices = (
        (FIXED, _('Fixed')),
        (ANNIVERSARY, _('Anniversary')),
    )
    schedule = models.CharField(_("Plan Recrurring Schedule"), max_length=16, default=ANNIVERSARY, 
        choices=schedule_choices,
        help_text=_("Choose if period should be at the end of each Month, or 30 days period")
        ) 
    is_rollover = models.BooleanField(_("Data rollover"), 
        default=True, 
        help_text=_(
            "New data will be added to the remaining data of the current subscription")
        )
    is_invoice_required = models.BooleanField(_("Requires Invoice"), 
        default=True, 
        help_text=_(
            "If this flag is enabled, it means invoice will be created for this plan.")
        )
    is_payment_required = models.BooleanField(_("Requires payment"), 
        default=True, 
        help_text=_(
            "If this flag is enabled, it means that a user that signs up with this plan is required to perform a payment.")
        )
    radius_group = models.ForeignKey('openwisp_radius.RadiusGroup', on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('RADIUS group:'), related_name="plan_radius",
        )
    temp_radius_group = models.ForeignKey('openwisp_radius.RadiusGroup', on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('Temporary RADIUS group:'), related_name="plan_temp_radius",
        )

    plan_cost = models.DecimalField(_('Plan Cost'), max_digits=7, decimal_places=2, db_index=True,
        blank=True,
        null=True,
        )
    plan_setup_cost = models.DecimalField(_('Plan Setup Cost'), max_digits=7, decimal_places=2, db_index=True,
        blank=True,
        null=True,
        )
    plan_tax = models.DecimalField(_('Plan Tax'), max_digits=7, decimal_places=2,
        blank=True,
        null=True,
        )  
    plan_currency = models.CharField(_('Plan Currency'), max_length=16, blank=True, null=True) 
      
    # Denormalised plan rating - used by reviews app.
    # Plan has no ratings if rating is None
    rating = models.FloatField(_('Rating'), null=True, editable=False) 

    class Meta(AbstractPlan.Meta):
        abstract = False
        swappable = swappable_setting("plans", "Plan")


class BillingInfo(AbstractBillingInfo):
    class Meta(AbstractBillingInfo.Meta):
        abstract = False
        swappable = swappable_setting("plans", "BillingInfo")


class UserPlan(AbstractUserPlan):
    class Meta(AbstractUserPlan.Meta):
        abstract = False
        swappable = swappable_setting("plans", "UserPlan")


class Pricing(AbstractPricing):
    class Meta(AbstractPricing.Meta):
        abstract = False
        swappable = swappable_setting("plans", "Pricing")


class PlanPricing(AbstractPlanPricing):
    class Meta(AbstractPlanPricing.Meta):
        abstract = False
        swappable = swappable_setting("plans", "PlanPricing")


class Quota(AbstractQuota):
    class Meta(AbstractQuota.Meta):
        abstract = False
        swappable = swappable_setting("plans", "Quota")


class PlanQuota(AbstractPlanQuota):
    class Meta(AbstractPlanQuota.Meta):
        abstract = False
        swappable = swappable_setting("plans", "PlanQuota")


class Order(AbstractOrder):
    class Meta(AbstractOrder.Meta):
        abstract = False
        swappable = swappable_setting("plans", "Order")


class Invoice(AbstractInvoice):
    class Meta(AbstractInvoice.Meta):
        abstract = False
        swappable = swappable_setting("plans", "Invoice")


class RecurringUserPlan(AbstractRecurringUserPlan):
    class Meta(AbstractRecurringUserPlan.Meta):
        abstract = False
        swappable = swappable_setting("plans", "RecurringUserPlan")


class BandwidthSettings(models.Model):
    plan = models.ForeignKey('plans.Plan', max_length=32, on_delete=models.CASCADE,
        related_name='bandwidth_for_plan'
        )
    name = models.CharField(_('Bandwidth Name'), max_length=32, 
        blank=True, 
        null=True,
        help_text=_("Bandwidth determines how much traffic can pass through, " 
                    "5 Mbps, means, user on this plan can transmit data up to a capacity/speed 5 Mbps")
        )
    bandwidth_up = models.CharField(_('Bandwidth Up'), max_length=8, blank=True, null=True)
    bandwidth_down = models.CharField(_('Bandwidth Down'), max_length=8, blank=True, null=True)

    MB, GB, TB = 'Megabyte (MB)', 'Gigabyte (GB)', 'Terabyte (TB)'
    traffic_unit_choices = (
        (MB, _('Megabyte (MB)')),
        (GB, _('Gigabyte (GB)')), 
        (TB, _('Terabyte (TB)')),
    )
    traffic_unit  = models.CharField(_("Plan Unit"), max_length=16, default=GB, choices=traffic_unit_choices)
    traffic_total = models.CharField(_('Traffic Total'), max_length=32, 
        blank=True, 
        null=True,
        help_text=_("The total traffic/data allowed to use")
        )
    plan_refill_cost = models.DecimalField('Plan Refill Cost', max_digits=7, decimal_places=2, 
        blank=True,
        null=True,
        )

    class Meta:
        ordering = ['name']
        verbose_name = _("Bandwidth Settings")
        verbose_name_plural = _("Bandwidth Settings")

    def __str__(self):
        return self.plan.name
    


# ----------------------------------------------------------- Plan payment
class Payment(BasePayment):
    order: Order = models.ForeignKey(
        settings.PLANS_ORDER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    transaction_fee: models.DecimalField = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        default=Decimal("0.0"),
    )
    autorenewed_payment: models.BooleanField = models.BooleanField(
        default=False,
    )

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["status", "transaction_id"]),
        ]

    def clean(self):
        if self.order.status == Order.STATUS.COMPLETED:
            confirmed_payment_count = self.order.payment_set.exclude(pk=self.pk)
            confirmed_payment_count = confirmed_payment_count.filter(
                status=PaymentStatus.CONFIRMED
            ).count()
            if self.status != PaymentStatus.CONFIRMED and confirmed_payment_count == 0:
                raise ValidationError(
                    {
                        "status": "Can't leave confirmed order without any confirmed payment. "
                        "Please change Order first if you still want to perform this change.",
                    },
                )

    def save(self, **kwargs):
        if "payu" in self.variant:
            # TODO: base this on actual payment methods and currency fees on PayU
            # or even better on real PayU info
            self.transaction_fee = self.total * Decimal("0.029") + Decimal("0.05")
        elif hasattr(self, "extra_data") and self.extra_data:
            extra_data = json.loads(self.extra_data)
            if "response" in extra_data:
                transactions = extra_data["response"]["transactions"]
                for transaction in transactions:
                    related_resources = transaction["related_resources"]
                    if len(related_resources) == 1:
                        sale = related_resources[0]["sale"]
                        if "transaction_fee" in sale:
                            self.transaction_fee = Decimal(
                                sale["transaction_fee"]["value"]
                            )
                        else:
                            logger.warning(
                                "Payment fee not included",
                                extra={
                                    "extra_data": extra_data,
                                },
                            )
        ret_val = super().save(**kwargs)
        return ret_val

    def get_failure_url(self):
        return reverse("order_payment_failure", kwargs={"pk": self.order.pk})

    def get_success_url(self):
        return reverse("order_payment_success", kwargs={"pk": self.order.pk})

    def get_payment_url(self):
        return reverse("payment_details", kwargs={"payment_id": self.pk})

    def get_purchased_items(self):
        yield PurchasedItem(
            name=self.description,
            sku=self.order.pk,
            quantity=1,
            price=self.order.amount,
            tax_rate=(1 + self.order.tax / 100) if self.order.tax else 1,
            currency=self.currency,
        )

    def get_renew_token(self):
        """
        Get the recurring payments renew token for user of this payment
        Used by PayU provider for now
        """
        try:
            recurring_plan = self.order.user.userplan.recurring
            if (
                recurring_plan.token_verified
                and self.variant == recurring_plan.payment_provider
            ):
                return recurring_plan.token
        except ObjectDoesNotExist:
            pass
        return None

    def set_renew_token(
        self,
        token,
        card_expire_year=None,
        card_expire_month=None,
        card_masked_number=None,
        automatic_renewal=True,
    ):
        """
        Store the recurring payments renew token for user of this payment
        The renew token is string defined by the provider
        Used by PayU provider for now
        """
        self.order.user.userplan.set_plan_renewal(
            order=self.order,
            token=token,
            payment_provider=self.variant,
            card_expire_year=card_expire_year,
            card_expire_month=card_expire_month,
            card_masked_number=card_masked_number,
            has_automatic_renewal=automatic_renewal,
        )


@receiver(status_changed, sender=Payment)
def change_payment_status(sender, *args, **kwargs):
    payment = kwargs["instance"]
    order = payment.order
    if payment.status == PaymentStatus.CONFIRMED:
        if hasattr(order.user.userplan, "recurring"):
            order.user.userplan.recurring.token_verified = True
            order.user.userplan.recurring.save()
        order.complete_order()
    if order.status != Order.STATUS.COMPLETED and payment.status not in (
        PaymentStatus.CONFIRMED,
        PaymentStatus.WAITING,
        PaymentStatus.INPUT,
    ):
        order.status = Order.STATUS.CANCELED
        # In case django-simples-history is installed
        order._change_reason = f"Django-plans-payments: Payment status changed to {payment.status}"
        order.save()
        if hasattr(order.user.userplan, "recurring"):
            order.user.userplan.recurring.token_verified = False
            order.user.userplan.recurring.save()


@receiver(account_automatic_renewal)
def renew_accounts(sender, user, *args, **kwargs):
    userplan = user.userplan
    if (
        userplan.recurring.payment_provider in settings.PAYMENT_VARIANTS
        and userplan.recurring.has_automatic_renewal
    ):
        order = userplan.recurring.create_renew_order()

        payment = create_payment_object(
            userplan.recurring.payment_provider, order, autorenewed_payment=True
        )

        try:
            redirect_url = payment.auto_complete_recurring()
        except Exception as e:
            print(f"Exceptin during automatic renewal: {e}")
            logger.exception(
                "Exception during account renewal",
                extra={
                    "payment": payment,
                },
            )
            redirect_url = urljoin(
                get_base_url(),
                reverse(
                    "create_order_plan", kwargs={"pk": order.get_plan_pricing().pk}
                ),
            )

        if redirect_url != "success":
            print("CVV2/3DS code is required, enter it at %s" % redirect_url)
            send_template_email(
                [payment.order.user.email],
                "mail/renew_cvv_3ds_title.txt",
                "mail/renew_cvv_3ds_body.txt",
                {"redirect_url": redirect_url},
                get_user_language(payment.order.user),
            )
        if payment.status == PaymentStatus.CONFIRMED:
            order.complete_order()
