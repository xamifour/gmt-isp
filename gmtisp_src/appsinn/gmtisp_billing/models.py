import json
import logging
import warnings

from decimal import Decimal
from urllib.parse import urljoin

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.dispatch.dispatcher import receiver
from django.urls import reverse

from swapper import swappable_setting

from payments import PaymentStatus, PurchasedItem, get_payment_model
from payments.core import get_base_url
from payments.models import BasePayment
from payments.signals import status_changed

from openwisp_users.mixins import OrgMixin

from .contrib import get_user_language, send_template_email
from .signals import account_automatic_renewal

from .base.models import (
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
    AbstractBandwidthSettings,
    AbstractPlanBandwidthSettings,
    AbstractPayment,
)


logger = logging.getLogger(__name__)
# ----------------------------------------------------------- plans
class Plan(AbstractPlan):
    # Test existing fields can be modified
    default = models.BooleanField(
        help_text=AbstractPlan._meta.get_field('default').help_text,
        default=AbstractPlan._meta.get_field('default').default,
        null=True,
        blank=True,
    )

    class Meta(AbstractPlan.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'Plan')


class UserPlan(AbstractUserPlan):
    class Meta(AbstractUserPlan.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'UserPlan')


class RecurringUserPlan(AbstractRecurringUserPlan):
    class Meta(AbstractRecurringUserPlan.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'RecurringUserPlan')


class Pricing(AbstractPricing):
    class Meta(AbstractPricing.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'Pricing')


class PlanPricing(AbstractPlanPricing):
    class Meta(AbstractPlanPricing.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'PlanPricing')


class Quota(AbstractQuota):
    class Meta(AbstractQuota.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'Quota')


class PlanQuota(AbstractPlanQuota):
    class Meta(AbstractPlanQuota.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'PlanQuota')


class BandwidthSettings(AbstractBandwidthSettings):
    class Meta(AbstractBandwidthSettings.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'BandwidthSettings')


class PlanBandwidthSettings(AbstractPlanBandwidthSettings):
    class Meta(AbstractPlanBandwidthSettings.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'PlanBandwidthSettings')


class BillingInfo(AbstractBillingInfo):
    class Meta(AbstractBillingInfo.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'BillingInfo')


class Order(AbstractOrder):
    class Meta(AbstractOrder.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'Order')


class Invoice(AbstractInvoice):
    class Meta(AbstractInvoice.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'Invoice')


class Payment(AbstractPayment):
    class Meta(AbstractPayment.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'Payment')




# class Payment(OrgMixin, BasePayment):
#     order: Order = models.ForeignKey(
#         "gmtisp_billing.Order",
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#     )
#     transaction_fee: models.DecimalField = models.DecimalField(
#         max_digits=9,
#         decimal_places=2,
#         default=Decimal("0.0"),
#     )
#     autorenewed_payment: models.BooleanField = models.BooleanField(
#         default=False,
#     )

#     class Meta:
#         indexes = [
#             models.Index(fields=["status"]),
#             models.Index(fields=["status", "transaction_id"]),
#         ]

#     def save(self, **kwargs):
#         if "payu" in self.variant:
#             # TODO: base this on actual payment methods and currency fees on PayU
#             # or even better on real PayU info
#             self.transaction_fee = self.total * Decimal("0.029") + Decimal("0.05")
#         elif hasattr(self, "extra_data") and self.extra_data:
#             extra_data = json.loads(self.extra_data)
#             if "response" in extra_data:
#                 transactions = extra_data["response"]["transactions"]
#                 for transaction in transactions:
#                     related_resources = transaction["related_resources"]
#                     if len(related_resources) == 1:
#                         sale = related_resources[0]["sale"]
#                         if "transaction_fee" in sale:
#                             self.transaction_fee = Decimal(
#                                 sale["transaction_fee"]["value"]
#                             )
#                         else:
#                             logger.warning(
#                                 "Payment fee not included",
#                                 extra={
#                                     "extra_data": extra_data,
#                                 },
#                             )
#         ret_val = super().save(**kwargs)
#         return ret_val

#     def get_failure_url(self):
#         return reverse("order_payment_failure", kwargs={"pk": self.order.pk})

#     def get_success_url(self):
#         return reverse("order_payment_success", kwargs={"pk": self.order.pk})

#     def get_payment_url(self):
#         return reverse("payment_details", kwargs={"payment_id": self.pk})

#     def get_purchased_items(self):
#         yield PurchasedItem(
#             name=self.description,
#             sku=self.order.pk,
#             quantity=1,
#             price=self.order.amount,
#             tax_rate=(1 + self.order.tax / 100) if self.order.tax else 1,
#             currency=self.currency,
#         )

#     def get_renew_token(self):
#         """
#         Get the recurring payments renew token for user of this payment
#         Used by PayU provider for now
#         """
#         try:
#             recurring_plan = self.order.user.userplan.recurring
#             if (
#                 recurring_plan.token_verified
#                 and self.variant == recurring_plan.payment_provider
#             ):
#                 return recurring_plan.token
#         except ObjectDoesNotExist:
#             pass
#         return None

#     def set_renew_token(
#         self,
#         token,
#         card_expire_year=None,
#         card_expire_month=None,
#         card_masked_number=None,
#         # TODO: automatic_renewal deprecated. Remove in the next major release.
#         automatic_renewal=None,
#         # TODO: renewal_triggered_by=None deprecated. Set to TASK in the next major release.
#         renewal_triggered_by=None,
#     ):
#         """
#         Store the recurring payments renew token for user of this payment
#         The renew token is string defined by the provider
#         Used by PayU provider for now
#         """
#         if automatic_renewal is None and renewal_triggered_by is None:
#             automatic_renewal = True
#         if automatic_renewal is not None:
#             warnings.warn(
#                 "automatic_renewal is deprecated. Use renewal_triggered_by instead.",
#                 DeprecationWarning,
#             )
#         if renewal_triggered_by == "user":
#             renewal_triggered_by = AbstractRecurringUserPlan.RENEWAL_TRIGGERED_BY.USER
#         elif renewal_triggered_by == "task":
#             renewal_triggered_by = AbstractRecurringUserPlan.RENEWAL_TRIGGERED_BY.TASK
#         elif renewal_triggered_by == "other":
#             renewal_triggered_by = AbstractRecurringUserPlan.RENEWAL_TRIGGERED_BY.OTHER
#         elif renewal_triggered_by is None:
#             warnings.warn(
#                 "renewal_triggered_by=None is deprecated. "
#                 "Set an AbstractRecurringUserPlan.RENEWAL_TRIGGERED_BY instead.",
#                 DeprecationWarning,
#             )
#             renewal_triggered_by = (
#                 AbstractRecurringUserPlan.RENEWAL_TRIGGERED_BY.TASK
#                 if automatic_renewal
#                 else AbstractRecurringUserPlan.RENEWAL_TRIGGERED_BY.USER
#             )
#         else:
#             raise ValueError(f"Invalid renewal_triggered_by: {renewal_triggered_by}")

#         self.order.user.userplan.set_plan_renewal(
#             order=self.order,
#             token=token,
#             payment_provider=self.variant,
#             card_expire_year=card_expire_year,
#             card_expire_month=card_expire_month,
#             card_masked_number=card_masked_number,
#             renewal_triggered_by=renewal_triggered_by,
#         )


# @receiver(status_changed, sender=Payment)
# def change_payment_status(sender, *args, **kwargs):
#     payment = kwargs["instance"]
#     order = payment.order
#     if payment.status == PaymentStatus.CONFIRMED:
#         if hasattr(order.user.userplan, "recurring"):
#             order.user.userplan.recurring.token_verified = True
#             order.user.userplan.recurring.save()
#         order.complete_order()
#     if (
#         getattr(settings, "PLANS_PAYMENTS_RETURN_ORDER_WHEN_PAYMENT_REFUNDED", False)
#         and payment.status == PaymentStatus.REFUNDED
#     ):
#         order._change_reason = (
#             f"Django-plans-payments: Payment status changed to {payment.status}"
#         )
#         order.return_order()
#     elif order.status != Order.STATUS.COMPLETED and payment.status not in (
#         PaymentStatus.CONFIRMED,
#         PaymentStatus.WAITING,
#         PaymentStatus.INPUT,
#     ):
#         order.status = Order.STATUS.CANCELED
#         # In case django-simples-history is installed
#         order._change_reason = (
#             f"Django-plans-payments: Payment status changed to {payment.status}"
#         )
#         order.save()
#         if hasattr(order.user.userplan, "recurring"):
#             order.user.userplan.recurring.token_verified = False
#             order.user.userplan.recurring.save()


# @receiver(account_automatic_renewal)
# def renew_accounts(sender, user, *args, **kwargs):
#     userplan = user.userplan
#     if (
#         userplan.recurring.payment_provider in settings.PAYMENT_VARIANTS
#         and userplan.recurring.renewal_triggered_by
#         == AbstractRecurringUserPlan.RENEWAL_TRIGGERED_BY.TASK
#     ):
#         order = userplan.recurring.create_renew_order()

#         payment = create_payment_object(
#             userplan.recurring.payment_provider, order, autorenewed_payment=True
#         )

#         try:
#             redirect_url = payment.auto_complete_recurring()
#         except Exception as e:
#             print(f"Exceptin during automatic renewal: {e}")
#             logger.exception(
#                 "Exception during account renewal",
#                 extra={
#                     "payment": payment,
#                 },
#             )
#             redirect_url = urljoin(
#                 get_base_url(),
#                 reverse(
#                     "create_order_plan", kwargs={"pk": order.get_plan_pricing().pk}
#                 ),
#             )

#         if redirect_url != "success":
#             print("CVV2/3DS code is required, enter it at %s" % redirect_url)
#             send_template_email(
#                 [payment.order.user.email],
#                 "mail/renew_cvv_3ds_title.txt",
#                 "mail/renew_cvv_3ds_body.txt",
#                 {"redirect_url": redirect_url},
#                 get_user_language(payment.order.user),
#             )
#         if payment.status == PaymentStatus.CONFIRMED:
#             order.complete_order()