import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from swapper import swappable_setting

from .base.models import (
    AbstractBillingInfo,
    AbstractInvoice,
    AbstractOrder,
    AbstractPlan,
    AbstractPlanQuota,
    AbstractQuota,
    AbstractRecurringUserPlan,
    AbstractUserPlan,
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


class Quota(AbstractQuota):
    class Meta(AbstractQuota.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'Quota')


class PlanQuota(AbstractPlanQuota):
    class Meta(AbstractPlanQuota.Meta):
        abstract = False
        swappable = swappable_setting('gmtisp_billing', 'PlanQuota')


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
