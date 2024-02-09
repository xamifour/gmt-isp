from django.db import models
from django.utils.translation import gettext_lazy as _

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

    There's three kinds of gmt_subscriptions; they're distinguished by the structure
    field.

    - A stand alone plan. Regular plan that lives by itself.
    - A child plan. All child gmt_subscriptions have a parent plan. They're a
      specific version of the parent.
    - A parent plan. It essentially represents a set of gmt_subscriptions.

    An example could be a yoga course, which is a parent plan. The different
    times/locations of the courses would be associated with the child gmt_subscriptions.
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