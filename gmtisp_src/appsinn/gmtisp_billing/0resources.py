You should wait until i tell you what to do with them.

# config.py

# TODO use django-conf
from django.conf import settings

TAX = getattr(settings, "PLANS_TAX", None)
TAXATION_POLICY = getattr(
    settings, "PLANS_TAXATION_POLICY", "gmtisp_billing.taxation.TAXATION_POLICY"
)
APP_VERBOSE_NAME = getattr(settings, "PLANS_APP_VERBOSE_NAME", "billing")


# context_processors.py
from django.urls import reverse

from .base.models import AbstractUserPlan

UserPlan = AbstractUserPlan.get_concrete_model()


def account_status(request):
    """
    Set following ``RequestContext`` variables:

     * ``ACCOUNT_EXPIRED = boolean``, account was expired state,
     * ``ACCOUNT_NOT_ACTIVE = boolean``, set when account is not expired, but it is over quotas so it is
                                        not active
     * ``EXPIRE_IN_DAYS = integer``, number of days to account expiration,
     * ``EXTEND_URL = string``, URL to account extend page.
     * ``ACTIVATE_URL = string``, URL to account activation needed if  account is not active

    """

    if hasattr(request, "user") and request.user.is_authenticated:
        try:
            return {
                "ACCOUNT_EXPIRED": request.user.userplan.is_expired(),
                "ACCOUNT_NOT_ACTIVE": (
                    not request.user.userplan.is_active()
                    and not request.user.userplan.is_expired()
                ),
                "EXPIRE_IN_DAYS": request.user.userplan.days_left(),
                "EXTEND_URL": reverse("current_plan"),
                "ACTIVATE_URL": reverse("account_activation"),
            }
        except UserPlan.DoesNotExist:
            pass
    return {}


# contrib.py
import logging

from django.apps import apps
from django.conf import settings
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.utils import translation

from .signals import user_language

email_logger = logging.getLogger("emails")


def send_template_email(recipients, title_template, body_template, context, language):
    """Sends e-mail using templating system"""

    send_emails = getattr(settings, "SEND_PLANS_EMAILS", True)
    if not send_emails:
        return

    site_name = getattr(settings, "SITE_NAME", "Please define settings.SITE_NAME")
    domain = getattr(settings, "SITE_URL", None)

    if domain is None:
        try:
            Site = apps.get_model("sites", "Site")
            current_site = Site.objects.get_current()
            site_name = current_site.name
            domain = current_site.domain
        except LookupError:
            pass

    context.update(
        {"site_name": site_name, "site_domain": domain, "site": current_site}
    )

    if language is not None:
        translation.activate(language)

    mail_title_template = loader.get_template(title_template)
    mail_body_template = loader.get_template(body_template)
    title = mail_title_template.render(context).strip()
    body = mail_body_template.render(context)
    try:
        mail_body_template_html = loader.get_template(
            body_template.replace(".txt", ".html")
        )
        html_body = mail_body_template_html.render(context)
    except TemplateDoesNotExist:
        html_body = None

    try:
        email_from = getattr(settings, "DEFAULT_FROM_EMAIL")
    except AttributeError:
        raise ImproperlyConfigured(
            "DEFAULT_FROM_EMAIL setting needed for sending e-mails"
        )

    mail.send_mail(title, body, email_from, recipients, html_message=html_body)

    if language is not None:
        translation.deactivate()

    email_logger.info(
        "Email (%s) sent to %s\nTitle: %s\n%s\n\n" % (language, recipients, title, body)
    )


def get_user_language(user):
    """Simple helper that will fire django signal in order
    to get User language possibly given by other part of application.
    :param user:
    :return: string or None
    """
    return_value = {}
    user_language.send(sender=user, user=user, return_value=return_value)
    return return_value.get("language")


# enumeration.py
import six


class Enumeration(object):
    """
    A small helper class for more readable enumerations,
    and compatible with Django's choice convention.
    You may just pass the instance of this class as the choices
    argument of model/form fields.

    Example:
            MY_ENUM = Enumeration([
                    (100, 'MY_NAME', 'My verbose name'),
                    (200, 'MY_AGE', 'My verbose age'),
            ])
            assert MY_ENUM.MY_AGE == 200
            assert MY_ENUM[1] == (200, 'My verbose age')
    """

    def __init__(self, enum_list):
        self.enum_list_full = enum_list
        self.enum_list = [(item[0], item[2]) for item in enum_list]
        self.enum_dict = {}
        self.enum_code = {}
        self.enum_display = {}
        for item in enum_list:
            self.enum_dict[item[1]] = item[0]
            self.enum_display[item[0]] = item[2]
            self.enum_code[item[0]] = item[1]

    def __contains__(self, v):
        return v in self.enum_list

    def __len__(self):
        return len(self.enum_list)

    def __getitem__(self, v):
        if isinstance(v, six.string_types):
            return self.enum_dict[v]
        elif isinstance(v, int):
            return self.enum_list[v]

    def __getattr__(self, name):
        try:
            return self.enum_dict[name]
        except KeyError:
            raise AttributeError

    def __iter__(self):
        return self.enum_list.__iter__()

    def __repr__(self):
        return "Enum(%s)" % self.enum_list_full.__repr__()

    def get_display_name(self, v):
        return self.enum_display[v]

    def get_display_code(self, v):
        return self.enum_code[v]


# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext

from .utils import get_country_code
from .models import Plan, BillingInfo, Order, PlanPricing, Payment



# class PlanForm(forms.ModelForm):
#     class Meta:
#         model = Plan
#         fields = '__all__'  # Use __all__ to include all fields from the model

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         instance = kwargs.get('instance')
#         if instance:  # Edit mode
#             self.fields['name'].widget.attrs['readonly'] = True
#             self.fields['slug'].widget.attrs['readonly'] = True


class OrderForm(forms.Form):
    plan_pricing = forms.ModelChoiceField(
        queryset=PlanPricing.objects.all(), widget=HiddenInput, required=True
    )


class CreateOrderForm(forms.ModelForm):
    """
    This form is intentionally empty as all values for Order object creation need to be computed inside view

    Therefore, when implementing for example a rabat coupons, you can add some fields here
     and create "recalculate" button.
    """

    class Meta:
        model = Order
        fields = tuple()


class BillingInfoForm(forms.ModelForm):
    class Meta:
        model = BillingInfo
        exclude = ("user",)

    def __init__(self, *args, request=None, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        if not self.instance.country:
            self.fields["country"].initial = get_country_code(request)
        return ret_val

    def clean(self):
        cleaned_data = super(BillingInfoForm, self).clean()

        try:
            cleaned_data["tax_number"] = BillingInfo.clean_tax_number(
                cleaned_data["tax_number"], cleaned_data.get("country", None)
            )
        except ValidationError as e:
            self._errors["tax_number"] = e.messages

        return cleaned_data


class BillingInfoWithoutShippingForm(BillingInfoForm):
    class Meta:
        model = BillingInfo
        exclude = (
            "user",
            "shipping_name",
            "shipping_street",
            "shipping_zipcode",
            "shipping_city",
        )


class FakePaymentsForm(forms.Form):
    status = forms.ChoiceField(
        choices=Order.STATUS, required=True, label=gettext("Change order status to")
    )


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['order', 'amount', 'currency', 'status', 'payment_method']


# importer.py
def import_name(name):
    """import module given by str or pass the module if it is not str"""
    if isinstance(name, str):
        components = name.split(".")
        mod = __import__(
            ".".join(components[0:-1]), globals(), locals(), [components[-1]]
        )
        return getattr(mod, components[-1])
    else:
        return name


# listners.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from .signals import activate_user_plan, order_completed
from .models import Plan, UserPlan, Order, Invoice
User = get_user_model()

@receiver(post_save, sender=Order)
def create_proforma_invoice(sender, instance, created, **kwargs):
    """
    For every Order if there are defined billing_data creates invoice proforma,
    which is an order confirmation document
    """
    if created:
        Invoice.create(instance, Invoice.INVOICE_TYPES["PROFORMA"])


@receiver(order_completed)
def create_invoice(sender, **kwargs):
    Invoice.create(sender, Invoice.INVOICE_TYPES["INVOICE"])


@receiver(post_save, sender=Invoice)
def send_invoice_by_email(sender, instance, created, **kwargs):
    if created:
        instance.send_invoice_by_email()


@receiver(post_save, sender=User)
def set_default_user_plan(sender, instance, created, **kwargs):
    """
    Creates default plan for the new user but also extending an account for default grace period.
    """

    if created:
        UserPlan.create_for_user(instance)


# Hook to django-registration to initialize plan automatically after user has confirm account


@receiver(activate_user_plan)
def initialize_plan_generic(sender, user, **kwargs):
    try:
        user.userplan.initialize()
    except UserPlan.DoesNotExist:
        return


try:
    from registration.signals import user_activated

    @receiver(user_activated)
    def initialize_plan_django_registration(sender, user, request, **kwargs):
        try:
            user.userplan.initialize()
        except UserPlan.DoesNotExist:
            return

except ImportError:
    pass


# Hook to django-getpaid if it is installed
try:
    from getpaid.signals import user_data_query

    @receiver(user_data_query)
    def set_user_email_for_getpaid(sender, order, user_data, **kwargs):
        user_data["email"] = order.user.email

except ImportError:
    pass


# mixins.py
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View


class LoginRequired(View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequired, self).dispatch(*args, **kwargs)


class UserObjectsOnlyMixin(object):
    def get_queryset(self):
        return (
            super(UserObjectsOnlyMixin, self)
            .get_queryset()
            .filter(user=self.request.user)
        )

# plan_change.py
from decimal import Decimal


class PlanChangePolicy(object):
    def _calculate_day_cost(self, plan, period):
        """
        Finds most fitted plan pricing for a given period, and calculate day cost
        """
        if plan.is_free():
            # If plan is free then cost is always 0
            return 0

        plan_pricings = plan.planpricing_set.order_by(
            "-pricing__period"
        ).select_related("pricing")
        selected_pricing = None
        for plan_pricing in plan_pricings:
            selected_pricing = plan_pricing
            if plan_pricing.pricing.period <= period:
                break

        if selected_pricing:
            return (selected_pricing.price / selected_pricing.pricing.period).quantize(
                Decimal("1.00")
            )

        raise ValueError("Plan %s has no pricings." % plan)

    def _calculate_final_price(self, period, day_cost_diff):
        if day_cost_diff is None:
            return None
        else:
            return period * day_cost_diff

    def get_change_price(self, plan_old, plan_new, period):
        """
        Calculates total price of plan change. Returns None if no payment is required.
        """
        if period is None or period < 1:
            return None

        plan_old_day_cost = self._calculate_day_cost(plan_old, period)
        plan_new_day_cost = self._calculate_day_cost(plan_new, period)

        if plan_new_day_cost <= plan_old_day_cost:
            return self._calculate_final_price(period, None)
        else:
            return self._calculate_final_price(
                period, plan_new_day_cost - plan_old_day_cost
            )


class StandardPlanChangePolicy(PlanChangePolicy):
    """
    This plan switch policy follows the rules:
        * user can downgrade a plan for free if the plan is
          cheaper or have exact the same price (additional constant charge can be applied)
        * user need to pay extra amount depending of plans price difference (additional constant charge can be applied)

    Change percent rate while upgrading is defined in ``StandardPlanChangePolicy.UPGRADE_PERCENT_RATE``

    Additional constant charges are:
        * ``StandardPlanChangePolicy.UPGRADE_CHARGE``
        * ``StandardPlanChangePolicy.FREE_UPGRADE``
        * ``StandardPlanChangePolicy.DOWNGRADE_CHARGE``

    .. note:: Example

        User has PlanA which costs monthly (30 days) 20 €. His account will expire in 23 days. He wants to change
        to PlanB which costs monthly (30 days) 50€. Calculations::

            PlanA costs per day 20 €/ 30 days = 0.67 €
            PlanB costs per day 50 €/ 30 days = 1.67 €
            Difference per day between PlanA and PlanB is 1.00 €
            Upgrade percent rate is 10%
            Constant upgrade charge is 0 €
            Switch cost is:
                       23 *            1.00 € *                  10% +                     0 € = 25.30 €
                days_left * cost_diff_per_day * upgrade_percent_rate + constant_upgrade_charge
    """

    UPGRADE_PERCENT_RATE = Decimal("10.0")
    UPGRADE_CHARGE = Decimal("0.0")
    DOWNGRADE_CHARGE = None
    FREE_UPGRADE = Decimal("0.0")

    def _calculate_final_price(self, period, day_cost_diff):
        if day_cost_diff is None:
            return self.DOWNGRADE_CHARGE
        cost = (
            period * day_cost_diff * (self.UPGRADE_PERCENT_RATE / 100 + 1)
            + self.UPGRADE_CHARGE
        ).quantize(Decimal("1.00"))
        if cost is None or cost < self.FREE_UPGRADE:
            return None
        else:
            return cost
        

# quota.py
def get_user_quota(user):
    """
    Tiny helper for getting quota dict for user
    If user has expired plan, return default plan or None
    """
    from .base.models import AbstractPlan

    Plan = AbstractPlan.get_concrete_model()
    plan = Plan.get_current_plan(user)
    return plan.get_quota_dict()


# signnals.py
from django.dispatch import Signal


order_started = Signal()
order_started.__doc__ = """
Sent after order was started (awaiting payment)
"""

order_completed = Signal()
order_completed.__doc__ = """
Sent after order was completed (payment accepted, account extended)
"""


user_language = Signal()
user_language.__doc__ = """
Sent to receive information about language for user account

sends arguments: 'user', 'language'
"""

account_automatic_renewal = Signal()
account_automatic_renewal.__doc__ = """
Try to renew the account automatically.
Should renew the user's UserPlan by recurring payments. If this succeeds, the plan should be extended.

sends arguments: 'user'
"""

account_expired = Signal()
account_expired.__doc__ = """
Sent on account expiration.
This signal is send regardless ``account_deactivated``
it only means that account has expired due to plan expire date limit.

sends arguments: 'user'
"""

account_deactivated = Signal()
account_deactivated.__doc__ = """
Sent on account deactivation, account is not operational (it could be not expired, but does not meet quota limits).

sends arguments: 'user'
"""

account_activated = Signal()
account_activated.__doc__ = """
Sent on account activation, account is now fully operational.

sends arguments: 'user'
"""
account_change_plan = Signal()
account_change_plan.__doc__ = """
Sent on account when plan was changed after order completion

sends arguments: 'user'
"""

activate_user_plan = Signal()
activate_user_plan.__doc__ = """
This signal should be called when user has succesfully registered (e.g. he activated account via e-mail activation).
If you are using django-registration there is no need to call this signal.

sends arguments: 'user'
"""


# tasks.py
import datetime
import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from .base.models import AbstractRecurringUserPlan
from .signals import account_automatic_renewal

User = get_user_model()
logger = logging.getLogger("plans.tasks")


def get_active_plans():
    return (
        User.objects.select_related("userplan")
        .filter(userplan__active=True)
        .exclude(userplan__expire=None)
    )


def autorenew_account(providers=None):
    logger.info("Started automatic account renewal")
    PLANS_AUTORENEW_BEFORE_DAYS = getattr(settings, "PLANS_AUTORENEW_BEFORE_DAYS", 0)
    PLANS_AUTORENEW_BEFORE_HOURS = getattr(settings, "PLANS_AUTORENEW_BEFORE_HOURS", 0)

    accounts_for_renewal = get_active_plans().filter(
        userplan__recurring__renewal_triggered_by=AbstractRecurringUserPlan.RENEWAL_TRIGGERED_BY.TASK,
        userplan__recurring__token_verified=True,
        userplan__expire__lt=datetime.date.today()
        + datetime.timedelta(
            days=PLANS_AUTORENEW_BEFORE_DAYS, hours=PLANS_AUTORENEW_BEFORE_HOURS
        ),
    )

    if providers:
        accounts_for_renewal = accounts_for_renewal.filter(
            userplan__recurring__payment_provider__in=providers
        )

    logger.info(f"{len(accounts_for_renewal)} accounts to be renewed.")

    for user in accounts_for_renewal.all():
        account_automatic_renewal.send(sender=None, user=user)
    return accounts_for_renewal


def expire_account():
    logger.info("Started account expiration")

    expired_accounts = get_active_plans().filter(
        userplan__expire__lt=datetime.date.today()
    )

    for user in expired_accounts.all():
        user.userplan.expire_account()

    notifications_days_before = getattr(settings, "PLANS_EXPIRATION_REMIND", [])

    if notifications_days_before:
        days = map(
            lambda x: datetime.date.today() + datetime.timedelta(days=x),
            notifications_days_before,
        )
        for user in User.objects.select_related("userplan").filter(
            userplan__active=True, userplan__expire__in=days
        ):
            user.userplan.remind_expire_soon()


# utils.py
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_country_code(request):
    if getattr(settings, "PLANS_GET_COUNTRY_FROM_IP", False):
        try:
            from geolite2 import geolite2

            reader = geolite2.reader()
            ip_address = get_client_ip(request)
            ip_info = reader.get(ip_address)
        except ModuleNotFoundError:
            ip_info = None

        if ip_info and "country" in ip_info:
            country_code = ip_info["country"]["iso_code"]
            return country_code
    return getattr(settings, "PLANS_DEFAULT_COUNTRY", None)


def get_currency():
    CURRENCY = getattr(settings, "PLANS_CURRENCY", "")
    if len(CURRENCY) != 3:
        raise ImproperlyConfigured(
            "PLANS_CURRENCY should be configured as 3-letter currency code."
        )
    return CURRENCY


def country_code_transform(country_code):
    """Transform country code to the code used by VIES"""
    transform_dict = {
        "GR": "EL",
    }
    return transform_dict.get(country_code, country_code)


# validators.py
import six
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.translation import gettext_lazy as _
# from django.apps import apps

from .importer import import_name
from .quota import get_user_quota


class QuotaValidator(object):
    """
    Base class for all Quota validators needed for account activation
    """

    required_to_activate = True
    default_quota_value = None

    @property
    def code(self):
        raise ImproperlyConfigured("Quota code name is not provided for validator")

    def get_quota_value(self, user, quota_dict=None):
        """
        Returns quota value for a given user
        """
        if quota_dict is None:
            quota_dict = get_user_quota(user)

        return quota_dict.get(self.code, self.default_quota_value)

    def get_error_message(self, quota_value, **kwargs):
        return "Plan validation error"

    def get_error_params(self, quota_value, **kwargs):
        return {
            "quota": quota_value,
            "validator_codename": self.code,
        }

    def __call__(self, user, quota_dict=None, **kwargs):
        """
        Performs validation of quota limit for a user account
        """
        raise NotImplementedError("Please implement specific QuotaValidator")

    def on_activation(self, user, quota_dict=None, **kwargs):
        """
        Hook for any action that validator needs to do while successful activation of the plan
        Most useful for validators not required to activate, e.g. some "option" is turned ON for user
        but when user downgrade plan this option should be turned OFF automatically rather than
        stops account activation
        """
        pass


class ModelCountValidator(QuotaValidator):
    """
    Validator that checks if there is no more than quota number of objects given model
    """

    @property
    def model(self):
        raise ImproperlyConfigured("ModelCountValidator requires model name")

    def get_queryset(self, user):
        return self.model.objects.all()

    def get_error_message(self, quota_value, **kwargs):
        return _(
            "Limit of %(model_name_plural)s exceeded. The limit is %(quota)s items."
        )

    def get_error_params(self, quota_value, total_count, **kwargs):
        return {
            "quota": quota_value,
            "model_name_plural": self.model._meta.verbose_name_plural.title().lower(),
            "validator_codename": self.code,
            "total_count": total_count,
        }

    def __call__(self, user, quota_dict=None, **kwargs):
        quota = self.get_quota_value(user, quota_dict)
        total_count = self.get_queryset(user).count() + kwargs.get("add", 0)
        if quota is not None and total_count > quota:
            raise ValidationError(
                message=self.get_error_message(quota),
                params=self.get_error_params(quota, total_count),
            )


class ModelAttributeValidator(ModelCountValidator):
    """
    Validator checks if every obj.attribute value for a given model satisfy condition
    provided in check_attribute_value() method.

    .. warning::
        ModelAttributeValidator requires `get_absolute_url()` method on provided model.
    """

    @property
    def attribute(self):
        raise ImproperlyConfigured(
            "ModelAttributeValidator requires defining attribute name"
        )

    def check_attribute_value(self, attribute_value, quota_value):
        # default is to value is <= limit
        return attribute_value <= quota_value

    def get_error_message(self, quota_value, **kwargs):
        return _("Following %(model_name_plural)s are not in limits: %(objects)s")

    def get_error_params(self, quota_value, total_count, **kwargs):
        return {
            "quota": quota_value,
            "validator_codename": self.code,
            "model_name_plural": self.model._meta.verbose_name_plural.title().lower(),
            "objects": ", ".join(
                map(
                    lambda o: '<a href="%s">%s</a>' % (o.get_absolute_url(), six.u(o)),
                    kwargs["not_valid_objects"],
                )
            ),
        }

    def __call__(self, user, quota_dict=None, **kwargs):
        quota_value = self.get_quota_value(user, quota_dict)
        not_valid_objects = []
        if quota_value is not None:
            for obj in self.get_queryset(user):
                if not self.check_attribute_value(
                    getattr(obj, self.attribute), quota_value
                ):
                    not_valid_objects.append(obj)
        if not_valid_objects:
            raise ValidationError(
                self.get_error_message(
                    quota_value, not_valid_objects=not_valid_objects
                ),
                self.get_error_params(quota_value, not_valid_objects=not_valid_objects),
            )


def plan_validation(user, plan=None, on_activation=False):
    """
    Validates validator that represents quotas in a given system
    :param user:
    :param plan:
    :return:
    """
    if plan is None:
        # if plan is not given, the default is to use current plan of the user
        plan = user.userplan.plan
    quota_dict = plan.get_quota_dict()
    validators = getattr(settings, "PLANS_VALIDATORS", {})
    validators = import_name(validators)
    errors = {
        "required_to_activate": [],
        "other": [],
    }

    for quota in validators:
        validator = import_name(validators[quota])

        if on_activation:
            validator.on_activation(user, quota_dict)
        else:
            try:
                validator(user, quota_dict)
            except ValidationError as e:
                if validator.required_to_activate:
                    errors["required_to_activate"].extend(e.messages)
                else:
                    errors["other"].extend(e.messages)
    return errors


Instuctions:
am going to share some django models and other codes for you to help me implement a tasks. You should wait until i tell you what to do with them.

create a view, that when a user click's "Buy Now" button of a plan the user is buying will assign 
that plan to the user after successful payment.

Note that,
1. user and plan are associated using class AbstractUserPlan
2. a plan is associated with RadiusGroup using a ForeignKey
3. AbstractPlanPricing is used to associate plan, pricing. it is also used to record order and the actual 
price of the plan
4. class AbstractRecurringUserPlan
5. use all the codes/models i have shared with you from the beginning


