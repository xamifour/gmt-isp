from __future__ import unicode_literals

import logging
import warnings
import re
import stdnum.eu.vat
from urllib.parse import urljoin
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.dispatch.dispatcher import receiver
try:
    from django.contrib.sites.models import Site
except RuntimeError:
    Site = None
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.template import Context
from django.template.base import Template
from django.urls import reverse
from django.utils import translation, timezone
# from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from django_countries.fields import CountryField
from sequences import get_next_value
from swapper import load_model

from openwisp_users.mixins import OrgMixin
from openwisp_utils.base import UUIDModel

from ..contrib import get_user_language, send_template_email
from ..enumeration import Enumeration
from ..importer import import_name
from ..signals import (
    account_activated,
    account_change_plan,
    account_deactivated,
    account_expired,
    order_completed,
    account_automatic_renewal,
)
from ..taxation.eu import EUTaxationPolicy
from ..utils import country_code_transform, get_country_code, get_currency
from ..validators import plan_validation


logger = logging.getLogger(__name__)
accounts_logger = logging.getLogger('accounts')

MAX_LENGTH = 67

# ----------------------------------------------------------- base mixin
class BaseMixin(UUIDModel):
    created  = models.DateTimeField(_('created'), auto_now_add=True, null=True, db_index=True, )
    modified = models.DateTimeField(_('modified'), auto_now=True, null=True)
    # created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='%(class)s_created_by')
    # modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='%(class)s_modified_by')
    
    class Meta:
        abstract = True

    @classmethod
    def get_concrete_model(cls):
        return load_model('gmtisp_billing', cls.__name__.replace('Abstract', ''))


# ----------------------------------------------------------- user usage
class AbstractUserUsage(OrgMixin, BaseMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    active_sessions = models.IntegerField(default=0)
    active_sub_sessions = models.IntegerField(default=0)
    total_download = models.BigIntegerField(default=0)
    total_upload = models.BigIntegerField(default=0)
    total_uptime = models.DurationField(_('Total Uptime'), default='0:00:00')
    attributes_details = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)

    class Meta:
        abstract = True
        ordering = ['-created']

    def __str__(self):
        return f"User ID: {self.user_id} - Download: {self.total_download} bytes, Upload: {self.total_upload} bytes"


# ----------------------------------------------------------- plans
class AbstractPlan(OrgMixin, BaseMixin):
    '''
    Single plan defined in the system. A plan can customized (referred to user) which means
    that only this user can purchase this plan and have it selected.

    Plan also can be visible and available. Plan is displayed on the list of currently available plans
    for user if it is visible. User cannot change plan to a plan that is not visible. Available means
    that user can buy a plan. If plan is not visible but still available it means that user which
    is using this plan already will be able to extend this plan again. If plan is not visible and not
    available, he will be forced then to change plan next time he extends an account.
    '''

    WHEN_START_CHOICES = [
        ('assigned', 'Assigned'),
        ('first-auth', 'First authentication'),
    ]
    name = models.CharField(_('name'), max_length=MAX_LENGTH, unique=True)
    slug = models.SlugField(_('slug'), max_length=MAX_LENGTH, blank=False, editable=True)
    description = models.CharField(_('description'), max_length=256, blank=True)
    name_for_users = models.CharField(_('name for users'), max_length=MAX_LENGTH, blank=True, null=True, help_text='Friendly name for user, e.g., Plan-100MB')
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, default='0.00', help_text='If price is 0.00, it means free/bonus')
    starts_when = models.CharField(_('starts when'), max_length=MAX_LENGTH, choices=WHEN_START_CHOICES, default='first-auth')
    override_shared_users = models.CharField(_('override shared users'), max_length=MAX_LENGTH, default='off')
    customized = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('customized:'))
    default = models.BooleanField(default=None, db_index=True, unique=True, null=True, help_text=_("Both 'Unknown' and 'No' means that the plan is not default"))
    available = models.BooleanField(_('Available:'), default=False, db_index=True, help_text=_('available for purchase'))
    visible = models.BooleanField(_('Visible:'), default=True, db_index=True, help_text=_('Is visible in current offer'))
    payment_required = models.BooleanField(_('Requires payment:'), default=True, db_index=True, help_text=_('require payment or not.'))
    rollover_allowed = models.BooleanField(_('Allow rollover:'), default=True, db_index=True, help_text=_('If true, Data purchasing now will be added to your remaining data, if you have any'))
    setup_cost = models.DecimalField(_('Plan Setup Cost'), max_digits=7, decimal_places=2, db_index=True, blank=True, null=True)
    BANDWIDTH, DATA, TIME = 'Bandwidth', 'Data', 'Time'
    VARIANT_CHOICES = ((BANDWIDTH, _('Bandwidth')), (DATA, _('Data')), (TIME, _('Time')))
    variant = models.CharField(_('Plan Variant:'), max_length=16, default=DATA, choices=VARIANT_CHOICES) 
    PREPAID, POSTPAID = 'Prepaid', 'Postpaid'
    TYPE_CHOICES = ((PREPAID, _('Prepaid')), (POSTPAID, _('Postpaid')))
    type = models.CharField(_('Plan Type:'), max_length=16, default=PREPAID, choices=TYPE_CHOICES)
    rating = models.FloatField(_('Rating'), blank=True, null=True, editable=False) 
    radius_group = models.ForeignKey('openwisp_radius.RadiusGroup', on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('RADIUS group:'), related_name='plan_radius_group')
    temp_radius_group = models.ForeignKey('openwisp_radius.RadiusGroup', on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('Temporary RADIUS group:'), related_name='plan_temp_radius_group')
    url = models.URLField(max_length=200, blank=True, help_text=_('Optional link to page with more information (for clickable plan table headers)'))

    class Meta:
        abstract = True
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')

    def get_absolute_url(self):
        return reverse('gmtisp_billing:plan_details', kwargs={'slug': self.slug})
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_default_plan(cls):
        """ Returns the default plan or None if no default plan exists."""
        default_plan = cls.objects.filter(default=True).first()
        return default_plan

    @classmethod
    def get_current_plan(cls, user):
        '''Get current plan for user. If userplan is expired, get default plan'''
        if (
            not user
            or user.is_anonymous
            or not hasattr(user, 'userplan')
            or user.userplan.is_expired()
        ):
            default_plan = cls.get_default_plan()
            if default_plan is None or not default_plan.is_free():
                raise ValidationError(_('User plan has expired'))
                # return None
            return default_plan
        return user.userplan.plan

    def get_quota_dict(self):
        quota_dict = dict(self.planquota_set.values_list('quota__name', 'quota__uptime_limit'))
        return quota_dict
    
    def get_plan_quota(self):
        return self.planquota_set.all()

    def get_plan_price(self):
        return self.price

    def get_plan_setup_cost(self):
        return self.setup_cost
    
    def is_free(self):
        return self.price == 0

    is_free.boolean = True

    def is_payment_required(self):
        if self.price == 0.00:
            return self.payment_required == False
        
    def is_visible(self):    
        if self.price == 0.00:
            return self.visible == False


class AbstractUserPlan(OrgMixin, BaseMixin):
    '''
    Currently selected plan for user account.
    '''
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('user'))
    plan = models.ForeignKey('gmtisp_billing.Plan', on_delete=models.CASCADE, verbose_name=_('Plan'), help_text=_('Plan that user is subscribed to.'))
    expire = models.DateTimeField( _('expire'), default=None, blank=True, null=True, db_index=True)
    active = models.BooleanField(_('active'), default=True, db_index=True)
    status = models.CharField(_('state'), max_length=MAX_LENGTH, blank=True, null=True, db_index=True)
    start_time = models.DateTimeField(_('start time'), null=True, blank=True)
    end_time = models.DateTimeField(_('end time'), null=True, blank=True)

    class Meta:
        abstract = True
        verbose_name = _('User plan')
        verbose_name_plural = _('Users plans')
    
    def __str__(self):
        return f'{self.user.username} - {self.plan.name}'
    
    def get_absolute_url(self):
        return reverse('gmtisp_billing:userplan-details', kwargs={'pk': self.pk})

    def is_active(self):
        return self.active

    def is_expired(self):
        if self.expire is None:
            return False
        return self.expire < timezone.now()  # Compare with current timezone-aware datetime

    def days_left(self):
        if self.expire is None:
            return None
        else:
            return (self.expire - timezone.now()).days

    def clean_activation(self):
        errors = plan_validation(self.user)
        if not errors['required_to_activate']:
            plan_validation(self.user, on_activation=True)
            self.activate()
        else:
            self.deactivate()
        return errors

    def activate(self):
        if not self.active:
            self.active = True
            self.save()
            account_activated.send(sender=self, user=self.user)

    def deactivate(self):
        if self.active:
            self.active = False
            self.save()
            account_deactivated.send(sender=self, user=self.user)

    def initialize(self):
        '''Set up user plan for first use'''
        if not self.is_active(): # if not active
            quota = self.plan.planquota_set.first() # Access the quota associated with the plan
            # Plans without quota.uptime_limit don't need to expire
            if self.expire is None and quota.uptime_limit is not None:
                self.expire = timezone.now() + timedelta(
                    days=getattr(settings, "PLANS_DEFAULT_GRACE_PERIOD", 30)
                )
            self.activate()  # this will call self.save()

    def get_plan_extended_from(self, plan):
        if plan.is_free():
            return None
        if not self.is_expired() and self.expire is not None and self.plan == plan:
            return self.expire
        return date.today()

    def has_automatic_renewal(self):
        return (
            hasattr(self, "recurring")
            and self.recurring.renewal_triggered_by
            != self.recurring.RENEWAL_TRIGGERED_BY.USER
            and self.recurring.token_verified
        )
    
    def get_plan_extended_until(self, plan, quota):
        if plan.is_free():
            return None
        if quota is None:
            return self.expire
        return self.get_plan_extended_from(plan) + quota.uptime_limit

    def plan_autorenew_at(self):
        '''
        Helper function which calculates when the plan autorenewal will occur
        '''
        if self.expire:
            plans_autorenew_before_days = getattr(
                settings, 'PLANS_AUTORENEW_BEFORE_DAYS', 0
            )
            plans_autorenew_before_hours = getattr(
                settings, 'PLANS_AUTORENEW_BEFORE_HOURS', 0
            )
            return self.expire - timedelta(
                days=plans_autorenew_before_days, hours=plans_autorenew_before_hours
            )

    def set_plan_renewal(self, order, has_automatic_renewal=None, renewal_triggered_by=None, **kwargs):
        '''
        Creates or updates plan renewal information for this userplan with given order
        '''
 
        if not hasattr(self, "recurring"):
            self.recurring = AbstractRecurringUserPlan.get_concrete_model()()

        if has_automatic_renewal is None and renewal_triggered_by is None:
            has_automatic_renewal = True
        if has_automatic_renewal is not None:
            warnings.warn(
                "has_automatic_renewal is deprecated. Use renewal_triggered_by instead.",
                DeprecationWarning,
            )
        if renewal_triggered_by is None:
            warnings.warn(
                "renewal_triggered_by=None is deprecated. "
                "Set an AbstractRecurringUserPlan.RENEWAL_TRIGGERED_BY instead.",
                DeprecationWarning,
            )
            renewal_triggered_by = (
                self.recurring.RENEWAL_TRIGGERED_BY.TASK
                if has_automatic_renewal
                else self.recurring.RENEWAL_TRIGGERED_BY.USER
            )

        # Erase values of all fields
        # We don't want to mix the old and new values
        self.recurring.set_all_fields_default()

        # Set new values
        self.recurring.user_plan = self
        self.recurring.quota = order.quota
        self.recurring.amount = order.amount
        self.recurring.tax = order.tax
        self.recurring.currency = order.currency
        self.recurring.renewal_triggered_by = renewal_triggered_by
        for k, v in kwargs.items():
            setattr(self.recurring, k, v)
        self.recurring.save()
        return self.recurring

    def extend_account(self, plan, quota):
        '''
        Manages extending account after plan or quota order
        :param plan: New plan to extend to
        :param quota: If quota is None, then the account will be only upgraded
        :return: Status of the extension operation
        '''
        status = False  # Flag; if extending account was successful?

        # Access the quota associated with the plan
        plan_quota = self.plan.planquota_set.first()
        if plan_quota is None:
            raise ValueError("No quota associated with the plan.")

        uptime_limit = plan_quota.quota.uptime_limit  # Ensure uptime_limit is accessed correctly

        # Get the new expiration date based on the plan and uptime_limit
        expire = self.get_plan_extended_until(plan, plan_quota.quota)  # Pass the quota object here

        if uptime_limit is None:
            self.plan = plan  # Process a plan change request (downgrade or upgrade)
            if self.expire is not None:
                self.expire = None

            self.save()
            account_change_plan.send(sender=self, user=self.user)
            if getattr(settings, 'PLANS_SEND_EMAILS_PLAN_CHANGED', True):
                mail_context = {'user': self.user, 'userplan': self, 'plan': plan}
                send_template_email(
                    [self.user.email],
                    'gmtisp_billing/mail/change_plan_title.txt',
                    'gmtisp_billing/mail/change_plan_body.txt',
                    mail_context,
                    get_user_language(self.user),
                )
            accounts_logger.info(
                "Account '%s' [id=%d] plan changed to '%s' [id=%d]"
                % (self.user, self.user.pk, plan, plan.pk)
            )
            status = True
        else:
            # Processing standard account extending procedure
            if self.plan == plan:
                status = True
            else:
                if not self.plan.is_free() and self.expire is None:
                    status = True
                elif not self.plan.is_free() and self.expire > date.today():
                    status = False
                    accounts_logger.warning(
                        "Account '%s' [id=%d] plan NOT changed to '%s' [id=%d]"
                        % (self.user, self.user.pk, plan, plan.pk)
                    )
                else:
                    status = True
                    account_change_plan.send(sender=self, user=self.user)
                    self.plan = plan

            if status:
                self.expire = expire
                self.save()
                accounts_logger.info(
                    "Account '%s' [id=%d] has been extended by %d days using plan '%s' [id=%d]"
                    % (self.user, self.user.pk, uptime_limit.days, plan, plan.pk)  # Use .days to get days from timedelta
                )
                if getattr(settings, 'PLANS_SEND_EMAILS_PLAN_EXTENDED', True):
                    mail_context = {
                        'user': self.user,
                        'userplan': self,
                        'plan': plan,
                        'quota': plan_quota,
                    }
                    send_template_email(
                        [self.user.email],
                        'gmtisp_billing/mail/extend_account_title.txt',
                        'gmtisp_billing/mail/extend_account_body.txt',
                        mail_context,
                        get_user_language(self.user),
                    )
        if status:
            self.clean_activation()
        return status


    def expire_account(self):
        '''manages account expiration'''

        self.deactivate()
        accounts_logger.info(
            "Account '%s' [id=%d] has expired" % (self.user, self.user.pk)
        )
        mail_context = {'user': self.user, 'userplan': self}
        send_template_email(
            [self.user.email],
            'gmtisp_billing/mail/expired_account_title.txt',
            'gmtisp_billing/mail/expired_account_body.txt',
            mail_context,
            get_user_language(self.user),
        )
        account_expired.send(sender=self, user=self.user)

    def remind_expire_soon(self):
        '''reminds about soon account expiration'''

        mail_context = {'user': self.user, 'userplan': self, 'days': self.days_left()}
        send_template_email(
            [self.user.email],
            'gmtisp_billing/mail/remind_expire_title.txt',
            'gmtisp_billing/mail/remind_expire_body.txt',
            mail_context,
            get_user_language(self.user),
        )

    @classmethod
    def create_for_user(cls, user):
        default_plan = AbstractPlan.get_concrete_model().get_default_plan()
        if default_plan is not None:
            UserPlan = AbstractUserPlan.get_concrete_model()
            return UserPlan.objects.create(
                user=user,
                plan=default_plan,
                active=False,
                expire=None,
            )

    @classmethod
    def create_for_users_without_plan(cls):
        userplans = get_user_model().objects.filter(userplan=None)
        for user in userplans:
            AbstractUserPlan.get_concrete_model().create_for_user(user)
        return userplans

    def get_current_plan(self):
        '''Tiny helper, very usefull in templates'''
        return AbstractPlan.get_concrete_model().get_current_plan(self.user)


class AbstractRecurringUserPlan(OrgMixin, BaseMixin):
    '''
    OneToOne model associated with UserPlan that stores information about the plan recurrence.
    More about recurring payments in docs.
    '''
    RENEWAL_TRIGGERED_BY = Enumeration(
        [
            (1, "OTHER", pgettext_lazy("Renewal triggered by", "other")),
            (2, "USER", pgettext_lazy("Renewal triggered by", "user")),
            (3, "TASK", pgettext_lazy("Renewal triggered by", "task")),
        ]
    )
    user_plan = models.OneToOneField('UserPlan', on_delete=models.CASCADE, related_name='recurring')
    token = models.CharField(_('recurring token'), max_length=200, default=None, null=True, blank=True, help_text=_('Token, that will be used for payment renewal. Depends on used payment provider'))
    payment_provider = models.CharField(_('payment provider'), max_length=200, default=None, null=True, blank=True, help_text=_('Provider, that will be used for payment renewal'))
    quota = models.ForeignKey('gmtisp_billing.Quota', default=None, null=True, blank=True, on_delete=models.CASCADE, help_text=_('Recurring quota'))
    amount = models.DecimalField(_('amount'), max_digits=7, decimal_places=2, db_index=True, null=True, blank=True)
    tax = models.DecimalField(_('tax'), max_digits=4, decimal_places=2, db_index=True, null=True, blank=True)  # Tax=None is when tax is not applicable
    currency = models.CharField(_('currency'), max_length=3)
    renewal_triggered_by = models.IntegerField(_("renewal triggered by"), choices=RENEWAL_TRIGGERED_BY, default=RENEWAL_TRIGGERED_BY.USER, db_index=True, help_text=_("The source of the associated plan's renewal (USER = user-initiated renewal, TASK = autorenew_account-task-initiated renewal, OTHER = renewal is triggered using another mechanism)."))
    _has_automatic_renewal_backup_deprecated = models.BooleanField(_("has automatic plan renewal"), db_column="has_automatic_renewal", default=False, help_text=_("Automatic renewal is enabled for associated plan. If False, the plan renewal can be still initiated by user."))  # TODO: Remove in the next major release.
    token_verified = models.BooleanField(_('token has been verified by payment'), default=False, help_text=_('The recurring token has been verified by at least one payment to be working.'))
    card_expire_year = models.IntegerField(null=True, blank=True)
    card_expire_month = models.IntegerField(null=True, blank=True)
    card_masked_number = models.CharField('CVV', null=True, blank=True, max_length=200)

    class Meta:
        abstract = True

    # TODO: has_automatic_renewal deprecated. Remove in the next major release.
    @property
    def has_automatic_renewal(self):
        warnings.warn(
            "has_automatic_renewal is deprecated. Use renewal_triggered_by instead.",
            DeprecationWarning,
        )
        return self.renewal_triggered_by != self.RENEWAL_TRIGGERED_BY.USER

    # TODO: has_automatic_renewal deprecated. Remove in the next major release.
    @has_automatic_renewal.setter
    def has_automatic_renewal(self, value):
        warnings.warn(
            "has_automatic_renewal is deprecated. Use renewal_triggered_by instead.",
            DeprecationWarning,
        )
        self.renewal_triggered_by = (
            self.RENEWAL_TRIGGERED_BY.TASK if value else self.RENEWAL_TRIGGERED_BY.USER
        )

    # TODO: has_automatic_renewal deprecated. Remove in the next major release.
    @has_automatic_renewal.deleter
    def has_automatic_renewal(self):
        warnings.warn(
            "has_automatic_renewal is deprecated. Use renewal_triggered_by instead.",
            DeprecationWarning,
        )
        del self.renewal_triggered_by

    def create_renew_order(self):
        '''
        Create order for plan renewal
        '''
        userplan = self.user_plan
        order = AbstractOrder.get_concrete_model().objects.create(
            user=userplan.user,
            plan=userplan.plan,
            quota=userplan.recurring.quota,
            amount=userplan.recurring.amount,
            tax=userplan.recurring.tax,  # Fallback value in case of VIES fault
            currency=userplan.recurring.currency,
        )
        order.recalculate(
            userplan.recurring.amount, userplan.user.billinginfo, use_default=False
        )
        order.save()

        # Save new value of tax
        userplan.recurring.tax = order.tax
        userplan.recurring.save()
        return order

    def set_all_fields_default(self):
        '''
        Set all fields to default values
        '''
        self.token = None
        self.payment_provider = None
        self.quota = None
        self.amount = None
        self.tax = None
        self.currency = None
        self.renewal_triggered_by = self.RENEWAL_TRIGGERED_BY.USER
        self.token_verified = False
        self.card_expire_year = None
        self.card_expire_month = None
        self.card_masked_number = None


# ----------------------------------------------------------- quota
class AbstractQuota(OrgMixin, BaseMixin):

    RESET_COUNTERS_INTERVAL = [
        ('disabled', 'Disabled'),
        ('monthly', 'Monthly'),
        ('weekly', 'Weekly'),
        ('daily', 'Daily'),
        ('hourly', 'Hourly'),
    ]
    
    VALIDITY_TYPE_CHOICES = [
        ('duration', 'Duration (days)'),
        ('time', 'Time (hours:minutes)'),
    ]

    class Priority(models.IntegerChoices):
        CRITICAL = 1, 'Critical'
        HIGH = 2, 'High'
        IMPORTANT = 3, 'Important'
        MEDIUM = 4, 'Medium'
        LOW = 5, 'Low'
        MINOR = 6, 'Minor'
        TRIVIAL = 7, 'Trivial'

    priority = models.IntegerField(choices=Priority.choices, default='4')
    name = models.CharField(max_length=MAX_LENGTH, unique=True, blank=True, null=True, help_text="limit-1gb")
    description = models.CharField(max_length=1024, blank=True, null=True)
    download_limit = models.BigIntegerField(default=0, help_text="")
    upload_limit = models.BigIntegerField(default=0, help_text="")
    transfer_limit = models.BigIntegerField(default=0, help_text="Total data limit, eq. 10GB")
    uptime_limit = models.DurationField(default='30 00:00:00', blank=True, null=True, help_text="'00:30:00' (30 minutes), '15 00:45:00' (15 days, 0 hours, 45 minutes, and 0 seconds), 'Empty' (no expiration)")
    rate_limit_rx = models.BigIntegerField(default=0, help_text="")
    rate_limit_tx = models.BigIntegerField(default=0, help_text="")
    rate_limit_min_rx = models.BigIntegerField(default=0, help_text="")
    rate_limit_min_tx = models.BigIntegerField(default=0, help_text="")
    rate_limit_priority = models.BigIntegerField(default=0, help_text="")
    rate_limit_burst_rx = models.BigIntegerField(default=0, help_text="")
    rate_limit_burst_tx = models.BigIntegerField(default=0, help_text="")
    rate_limit_burst_threshold_rx = models.BigIntegerField(default=0, help_text="")
    rate_limit_burst_threshold_tx = models.BigIntegerField(default=0, help_text="")
    rate_limit_burst_time_rx = models.BigIntegerField(default=0, help_text="")
    rate_limit_burst_time_tx = models.BigIntegerField(default=0, help_text="")
    reset_counters_start_time = models.DateTimeField(blank=True, null=True, help_text="")
    reset_counters_interval = models.CharField(max_length=MAX_LENGTH, choices=RESET_COUNTERS_INTERVAL, default='disabled', help_text="")
    is_boolean = models.BooleanField(_("is boolean"), default=False)
    url = models.CharField(
        max_length=200,
        blank=True,
        help_text=_(
            "Optional link to page with more information (for clickable quota table headers)"
        ),
    )


    class Meta:
        abstract = True
        verbose_name = _('Quota')
        verbose_name_plural = _('Quotas')
        
    def __str__(self):
        return self.name 

class PlanQuotaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('plan', 'quota')
    
class AbstractPlanQuota(OrgMixin, BaseMixin):
    plan  = models.ForeignKey('gmtisp_billing.Plan', on_delete=models.CASCADE)
    quota = models.ForeignKey('gmtisp_billing.Quota', on_delete=models.CASCADE)
    from_time = models.TimeField(default='00:00:00')
    till_time = models.TimeField(default='23:59:59')
    weekdays = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)  # Comma-separated weekdays

    objects = PlanQuotaManager()

    class Meta:
        abstract = True
        verbose_name = _('Plan quota')
        verbose_name_plural = _('Plans quotas')

    def __str__(self):
        return f'{self.plan.name} {self.quota}'
    
    def get_absolute_url(self):
        return reverse('admin:gmtisp_billing_planquota_change', args=[self.pk])

    
# ----------------------------------------------------------- billing info
class AbstractBillingInfo(OrgMixin, BaseMixin):
    '''
    Stores customer billing data needed to issue an invoice
    '''
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_('user'), on_delete=models.CASCADE)
    tax_number = models.CharField(_('VAT ID'), max_length=MAX_LENGTH, blank=True, db_index=True)
    name = models.CharField(_('name'), max_length=MAX_LENGTH, db_index=True)
    street = models.CharField(_('street'), max_length=MAX_LENGTH)
    zipcode = models.CharField(_('zip code'), max_length=MAX_LENGTH)
    city = models.CharField(_('city'), max_length=MAX_LENGTH)
    country = CountryField(_('country'))
    shipping_name = models.CharField(_('name (shipping)'), max_length=MAX_LENGTH, blank=True, help_text=_('optional'))
    shipping_street = models.CharField(_('street (shipping)'), max_length=MAX_LENGTH, blank=True, help_text=_('optional'))
    shipping_zipcode = models.CharField(_('zip code (shipping)'), max_length=MAX_LENGTH, blank=True, help_text=_('optional'))
    shipping_city = models.CharField(_('city (shipping)'), max_length=MAX_LENGTH, blank=True, help_text=_('optional'))
    shipping_country = CountryField(_('country (shipping)'), blank=True, help_text=_('optional'))

    class Meta:
        abstract = True
        verbose_name = _('Billing info')
        verbose_name_plural = _('Billing infos')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("gmtisp_billing:billing_info_detail", kwargs={"pk": self.pk})
    
    @staticmethod
    def get_full_tax_number(tax_number, country):
        number = tax_number
        if tax_number.startswith(country):
            number = tax_number[len(country) :]
        return country_code_transform(country) + number

    @staticmethod
    def clean_tax_number(tax_number, country):
        tax_number = re.sub(r'[^A-Z0-9]', '', tax_number.upper())

        country_str = tax_number[: len(country)]
        if country_str == country_code_transform(country):
            country = country_code_transform(country)

        if country_str.isalpha() and country_str != country:
            raise ValidationError(
                _("VAT ID country code doesn't corespond with country")
            )

        if tax_number and country:
            if country.lower() in stdnum.eu.vat.MEMBER_STATES:
                full_number = (
                    AbstractBillingInfo.get_concrete_model().get_full_tax_number(
                        tax_number, country
                    )
                )
                try:
                    return stdnum.eu.vat.validate(full_number)
                except stdnum.exceptions.ValidationError as e:
                    raise ValidationError(_(f"VAT ID is not correct: {e.message}"))

            return tax_number
        else:
            return ''


# ----------------------------------------------------------- order
class AbstractOrder(OrgMixin, BaseMixin):
    '''
    Order in this app supports only one item per order. This item is defined by
    plan and quota attributes. If both are defined the order represents buying
    an account extension.

    If only plan is provided (with quota set to None) this means that user purchased
    a plan upgrade.
    '''
    STATUS = Enumeration(
        [
            (1, 'NEW', pgettext_lazy('Order status', 'new')),
            (2, 'COMPLETED', pgettext_lazy('Order status', 'completed')),
            (3, 'NOT_VALID', pgettext_lazy('Order status', 'not valid')),
            (4, 'CANCELED', pgettext_lazy('Order status', 'canceled')),
            (5, 'RETURNED', pgettext_lazy('Order status', 'returned')),
        ]
    )
    flat_name = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('user'))
    plan = models.ForeignKey('gmtisp_billing.Plan', on_delete=models.CASCADE, verbose_name=_('plan'), related_name='plan_order')
    quota = models.ForeignKey('gmtisp_billing.Quota', blank=True, null=True, verbose_name=_('quota'), on_delete=models.CASCADE)  # if quota is None the order is upgrade plan, not buy new quota
    completed = models.DateTimeField(_('completed'), null=True, blank=True, db_index=True)
    plan_extended_from = models.DateField(_('plan extended from'), help_text=_('The plan was extended from this date'), null=True, blank=True)
    plan_extended_until = models.DateField(_('plan extended until'), help_text=_('The plan was extended until this date'), null=True, blank=True)
    amount = models.DecimalField(_('amount'), max_digits=7, decimal_places=2, db_index=True)
    tax = models.DecimalField(_('tax'), max_digits=4, decimal_places=2, db_index=True, null=True, blank=True)  # Tax=None is when tax is not applicable
    currency = models.CharField(_('currency'), max_length=3, default='GHS')
    status = models.IntegerField(_('status'), choices=STATUS, default=STATUS.NEW)

    class Meta:
        abstract = True
        ordering = ('-completed',)
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def __str__(self):
        return _('Order #: %(id)d') % {'id': self.id} # id formatted as a decimal integer

    def get_absolute_url(self):
        return reverse('order', kwargs={'pk': self.pk})
    
    @property
    def name(self):
        '''
        Support for two kind of Order names:
        * (preferred) dynamically generated from Plan and Quota (if flatname is not provided) (translatable)
        * (legacy) just return flat name, which is any text (not translatable)

        Flat names are only introduced for legacy system support, when you need to migrate old orders into
        django-plans and you cannot match Plan&Quota convention.
        '''
        if self.flat_name:
            return self.flat_name
        else:
            return '%s %s ' % (
                self.plan.name,
                '(upgrade)' if self.quota.name is None else '- %s' % self.quota.name,
            )

    def is_ready_for_payment(self):
        return self.status == self.STATUS.NEW and (timezone.now() - self.created).days < getattr(
            settings, 'PLANS_ORDER_EXPIRATION', 14
        )

    def get_plan_extended_from(self):
        return self.user.userplan.get_plan_extended_from(self.plan)

    def get_plan_extended_until(self):
        return self.user.userplan.get_plan_extended_until(self.plan, self.quota)

    @transaction.atomic()
    def complete_order(self):
        # Get locked order to ensure only one completed order is processed at a time
        order = (
            AbstractOrder.get_concrete_model()
            .objects.filter(id=self.id)
            .select_for_update()
            .get()
        )

        if order.completed is None:
            self.plan_extended_from = self.get_plan_extended_from()
            status = self.user.userplan.extend_account(self.plan, self.quota)
            self.plan_extended_until = self.user.userplan.expire
            order.completed = self.completed = timezone.now()
            if status:
                self.status = self.STATUS.COMPLETED
            else:
                self.status = self.STATUS.NOT_VALID
            self.save()
            order_completed.send(self)
            return True
        else:
            return False
        
    def return_order(self):
        if self.status != self.STATUS.RETURNED:
            if self.status == self.STATUS.COMPLETED:
                if self.quota is not None:
                    extended_from = self.plan_extended_from
                    if extended_from is None:
                        extended_from = self.completed
                    # Should never happen, but make sure we reduce for the same number of days as we extended.
                    if (
                        self.plan_extended_until is None
                        or extended_from is None
                        or self.plan_extended_until - extended_from
                        != timedelta(days=self.quota.uptime_limit)
                    ):
                        raise ValueError(
                            f"Invalid order state: completed={self.completed}, "
                            f"plan_extended_from={self.plan_extended_from}, "
                            f"plan_extended_until={self.plan_extended_until}, "
                            f"quota.uptime_limit={self.quota.uptime_limit}"
                        )
                self.user.userplan.reduce_account(self.quota)
            elif self.status != self.STATUS.NOT_VALID:
                raise ValueError(
                    f"Cannot return order with status other than COMPLETED and NOT_VALID: {self.status}"
                )
            self.status = self.STATUS.RETURNED
            self.save()

    def get_invoices_proforma(self):
        return AbstractInvoice.get_concrete_model().proforma.filter(order=self)

    def get_invoices(self):
        return AbstractInvoice.get_concrete_model().invoices.filter(order=self)

    def get_all_invoices(self):
        return self.invoice_set.order_by('issued', 'issued_duplicate', 'pk')
    
    def get_plan_quota(self):
        return AbstractPlanQuota.get_concrete_model().objects.get(
            plan=self.plan, quota=self.quota
        )
    def tax_total(self):
        if self.tax is None:
            return Decimal('0.00')
        else:
            return self.total() - self.amount

    def total(self):
        if self.tax is not None:
            return (Decimal(self.amount) * (Decimal(self.tax) + 100) / 100).quantize(Decimal('1.00'))
        else:
            return self.amount

    def recalculate(self, amount, billing_info, request=None, use_default=True):
        '''
        Calculates and return pre-filled Order
        '''
        self.amount = amount
        self.currency = get_currency()
        country = getattr(billing_info, 'country', None)
        if country is None:
            country = get_country_code(request)
        else:
            country = country.code
        if hasattr(billing_info, 'tax_number') and billing_info.tax_number:
            tax_number = AbstractBillingInfo.get_full_tax_number(
                billing_info.tax_number, country
            )
        else:
            tax_number = None
        # Calculating tax can be complex task (e.g. VIES webservice call)
        # To ensure that tax calculated on order preview will be the same on final order
        # tax rate is cached for a given billing data (as this value only depends on it)
        tax_session_key = 'tax_%s_%s' % (tax_number, country)
        request_successful = True
        if request:
            tax = request.session.get(tax_session_key)
        else:
            tax = None
        if tax is None:
            taxation_policy = getattr(settings, 'PLANS_TAXATION_POLICY', None)
            if not taxation_policy:
                raise ImproperlyConfigured('PLANS_TAXATION_POLICY is not set')
            taxation_policy = import_name(taxation_policy)
            tax, request_successful = taxation_policy.get_tax_rate(
                tax_number, country, request
            )
            tax = str(tax)
            # Because taxation policy could return None which clutters with saving this value
            # into cache, we use str() representation of this value
            if request and request_successful:
                request.session[tax_session_key] = tax
        if (
            use_default or request_successful
        ):  # Don't change the tax, if the request was not successful
            self.tax = Decimal(tax) if tax != 'None' else None


# ----------------------------------------------------------- invoices
class InvoiceManager(models.Manager):
    def get_queryset(self):
        return (
            super(InvoiceManager, self)
            .get_queryset()
            .filter(type=AbstractInvoice.INVOICE_TYPES['INVOICE'])
        )

class InvoiceProformaManager(models.Manager):
    def get_queryset(self):
        return (
            super(InvoiceProformaManager, self)
            .get_queryset()
            .filter(type=AbstractInvoice.INVOICE_TYPES['PROFORMA'])
        )

class InvoiceDuplicateManager(models.Manager):
    def get_queryset(self):
        return (
            super(InvoiceDuplicateManager, self)
            .get_queryset()
            .filter(type=AbstractInvoice.INVOICE_TYPES['DUPLICATE'])
        )

def get_initial_number(older_invoices):
    return (
        getattr(older_invoices.order_by('number').values('number').last(), 'number', 0)
        + 1
    )

class AbstractInvoice(OrgMixin, BaseMixin):
    '''
    Single invoice document.
    '''
    INVOICE_TYPES = Enumeration(
        [
            (1, 'INVOICE', _('Invoice')),
            (2, 'DUPLICATE', _('Invoice Duplicate')),
            (3, 'PROFORMA', pgettext_lazy('proforma', 'Order confirmation')),
        ]
    )
    objects = models.Manager()
    invoices = InvoiceManager()
    proforma = InvoiceProformaManager()
    duplicates = InvoiceDuplicateManager()

    class NUMBERING:
        '''Used as a choices for settings.PLANS_INVOICE_COUNTER_RESET'''

        DAILY = 1
        MONTHLY = 2
        ANNUALLY = 3

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'), on_delete=models.CASCADE)
    order = models.ForeignKey('gmtisp_billing.Order', verbose_name=_('order'), on_delete=models.CASCADE)
    number = models.IntegerField(db_index=True)
    full_number = models.CharField(max_length=MAX_LENGTH)
    type = models.IntegerField(choices=INVOICE_TYPES, default=INVOICE_TYPES.INVOICE, db_index=True)
    issued = models.DateField(db_index=True)
    issued_duplicate = models.DateField(db_index=True, null=True, blank=True)
    selling_date = models.DateField(db_index=True, null=True, blank=True)
    payment_date = models.DateField(db_index=True)
    unit_price_net = models.DecimalField(max_digits=7, decimal_places=2)
    quantity = models.IntegerField(default=1)
    total_net = models.DecimalField(max_digits=7, decimal_places=2)
    total = models.DecimalField(max_digits=7, decimal_places=2)
    tax_total = models.DecimalField(max_digits=7, decimal_places=2)
    tax = models.DecimalField(max_digits=4, decimal_places=2, db_index=True, null=True, blank=True)  # Tax=None is when tax is not applicable
    rebate = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal(0))
    currency = models.CharField(max_length=3, default='EUR')
    item_description = models.CharField(max_length=MAX_LENGTH)
    buyer_name = models.CharField(max_length=MAX_LENGTH, verbose_name=_('Name'), blank=True)
    buyer_street = models.CharField(max_length=MAX_LENGTH, verbose_name=_('Street'), blank=True)
    buyer_zipcode = models.CharField(max_length=MAX_LENGTH, verbose_name=_('Zip code'), blank=True)
    buyer_city = models.CharField(max_length=MAX_LENGTH, verbose_name=_('City'), blank=True)
    buyer_country = CountryField(verbose_name=_('Country'), default='PL', blank=True)
    buyer_tax_number = models.CharField(max_length=MAX_LENGTH, blank=True, verbose_name=_('TAX/VAT number'))
    shipping_name = models.CharField(max_length=MAX_LENGTH, verbose_name=_('Name'), blank=True)
    shipping_street = models.CharField(max_length=MAX_LENGTH, verbose_name=_('Street'), blank=True)
    shipping_zipcode = models.CharField(max_length=MAX_LENGTH, verbose_name=_('Zip code'), blank=True)
    shipping_city = models.CharField(max_length=MAX_LENGTH, verbose_name=_('City'), blank=True)
    shipping_country = CountryField(verbose_name=_('Country'), default='PL', blank=True)
    require_shipment = models.BooleanField(default=False, db_index=True)
    issuer_name = models.CharField(max_length=MAX_LENGTH, verbose_name=_('Name'))
    issuer_street = models.CharField(max_length=MAX_LENGTH, verbose_name=_('Street'))
    issuer_zipcode = models.CharField(max_length=MAX_LENGTH, verbose_name=_('Zip code'))
    issuer_city = models.CharField(max_length=MAX_LENGTH, verbose_name=_('City'))
    issuer_country = CountryField(verbose_name=_('Country'), default='PL')
    issuer_tax_number = models.CharField(max_length=MAX_LENGTH, blank=True, verbose_name=_('TAX/VAT number'))

    class Meta:
        abstract = True
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')

    def __str__(self):
        return self.full_number

    def get_absolute_url(self):
        return reverse('invoice_preview_html', kwargs={'pk': self.pk})

    def clean(self):
        if self.number is None:
            Invoice = self.get_concrete_model()
            invoice_counter_reset = getattr(
                settings, 'PLANS_INVOICE_COUNTER_RESET', Invoice.NUMBERING.MONTHLY
            )
            invoice_counter_reset_name = invoice_counter_reset

            # To avoid duplicates as well as gaps in the sequence, we are using django-sequences
            # to generate sequence number for each invoice
            # We keep the old sequence generating mechanism to get lower initial value,
            # so that the sequence will continue backward compatibly
            older_invoices = Invoice.objects.filter(type=self.type)
            initial_number = None
            if invoice_counter_reset == Invoice.NUMBERING.DAILY:
                invoice_counter_value = (
                    f'{self.issued.year}_{self.issued.month}_{self.issued.day}'
                )
                older_invoices = older_invoices.filter(issued=self.issued)
            elif invoice_counter_reset == Invoice.NUMBERING.MONTHLY:
                invoice_counter_value = f'{self.issued.year}_{self.issued.month}'
                older_invoices = older_invoices.filter(
                    issued__year=self.issued.year,
                    issued__month=self.issued.month,
                )
            elif invoice_counter_reset == Invoice.NUMBERING.ANNUALLY:
                invoice_counter_value = f'{self.issued.year}'
                older_invoices = older_invoices.filter(issued__year=self.issued.year)
            elif callable(invoice_counter_reset):
                invoice_counter_value, initial_number = invoice_counter_reset(self)
                invoice_counter_reset_name = 'call'
            else:
                raise ImproperlyConfigured(
                    'PLANS_INVOICE_COUNTER_RESET can be set only to these values: daily, monthly, yearly.'
                )

            # get initial value for backward compatibility
            if initial_number:
                self.initial_number = initial_number
            else:
                self.initial_number = get_initial_number(older_invoices)
            self.sequence_name = f'invoice_numbers_{self.type}_{invoice_counter_reset_name}_{invoice_counter_value}'

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.number is None:
                self.number = get_next_value(
                    self.sequence_name, initial_value=self.initial_number
                )
            super(AbstractInvoice, self).save(*args, **kwargs)

        # We need to generate full number based on what invoice sequence number actually ended up in DB
        self.refresh_from_db()
        if self.full_number == '':
            self.full_number = self.get_full_number()
        super(AbstractInvoice, self).save(update_fields=['full_number'])

    #    def validate_unique(self, exclude=None):
    #        super(Invoice, self).validate_unique(exclude)
    #        if self.type == Invoice.INVOICE_TYPES.INVOICE:
    #            if Invoice.objects.filter(order=self.order).count():
    #                raise ValidationError('Duplicate invoice for order')
    #        if self.type in (Invoice.INVOICE_TYPES.INVOICE, Invoice.INVOICE_TYPES.PROFORMA):
    #            pass

    def get_full_number(self):
        '''
        Generates on the fly invoice full number from template provided by ``settings.PLANS_INVOICE_NUMBER_FORMAT``.
        ``Invoice`` object is provided as ``invoice`` variable to the template, therefore all object fields
        can be used to generate full number format.

        .. warning::

            This is only used to prepopulate ``full_number`` field on saving new invoice.
            To get invoice full number always use ``full_number`` field.

        :return: string (generated full number)
        '''
        format = getattr(
            settings,
            'PLANS_INVOICE_NUMBER_FORMAT',
            '{{ invoice.number }}/'
            '{% if invoice.type == invoice.INVOICE_TYPES.PROFORMA %}PF{% else %}FV{% endif %}'
            "/{{ invoice.issued|date:'m/Y' }}",
        )
        return Template(format).render(Context({'invoice': self}))

    def set_issuer_invoice_data(self):
        '''
        Fills models object with issuer data copied from ``settings.PLANS_INVOICE_ISSUER``

        :raise: ImproperlyConfigured
        '''
        try:
            issuer = getattr(settings, 'PLANS_INVOICE_ISSUER')
        except Exception:
            raise ImproperlyConfigured(
                'Please set PLANS_INVOICE_ISSUER in order to make an invoice.'
            )
        self.issuer_name = issuer['issuer_name']
        self.issuer_street = issuer['issuer_street']
        self.issuer_zipcode = issuer['issuer_zipcode']
        self.issuer_city = issuer['issuer_city']
        self.issuer_country = issuer['issuer_country']
        self.issuer_tax_number = issuer['issuer_tax_number']

    def set_buyer_invoice_data(self, billing_info):
        '''
        Fill buyer invoice billing and shipping data by copy them from provided user's ``BillingInfo`` object.

        :param billing_info: BillingInfo object
        :type billing_info: BillingInfo
        '''
        self.buyer_name = billing_info.name
        self.buyer_street = billing_info.street
        self.buyer_zipcode = billing_info.zipcode
        self.buyer_city = billing_info.city
        self.buyer_country = billing_info.country
        self.buyer_tax_number = billing_info.tax_number

        self.shipping_name = billing_info.shipping_name or billing_info.name
        self.shipping_street = billing_info.shipping_street or billing_info.street
        self.shipping_zipcode = billing_info.shipping_zipcode or billing_info.zipcode
        self.shipping_city = billing_info.shipping_city or billing_info.city
        # TODO: Should allow shipping to other country? Not think so
        self.shipping_country = billing_info.country

    def copy_from_order(self, order):
        '''
        Filling orders details likes totals, taxes, etc and linking provided ``Order`` object with an invoice

        :param order: Order object
        :type order: Order
        '''
        self.order = order
        self.user = order.user
        self.unit_price_net = order.amount
        self.total_net = order.amount
        self.total = order.total()
        self.tax_total = order.total() - order.amount
        self.tax = order.tax
        self.currency = order.currency
        if Site is not None:
            self.item_description = '%s - %s' % (
                Site.objects.get_current().name,
                order.name,
            )
        else:
            self.item_description = order.name

    @classmethod
    def create(cls, order, invoice_type):
        language_code = get_user_language(order.user)

        if language_code is not None:
            translation.activate(language_code)

        BillingInfo = AbstractBillingInfo.get_concrete_model()
        try:
            billing_info = BillingInfo.objects.get(user=order.user)
        except BillingInfo.DoesNotExist:
            return

        day = date.today()
        pday = order.completed
        if invoice_type == cls.INVOICE_TYPES['PROFORMA']:
            pday = day + timedelta(days=14)

        invoice = cls(
            issued=day, selling_date=order.completed, payment_date=pday
        )  # FIXME: 14 - this should set accordingly to ORDER_TIMEOUT in days
        invoice.type = invoice_type
        invoice.copy_from_order(order)
        invoice.set_issuer_invoice_data()
        invoice.set_buyer_invoice_data(billing_info)
        invoice.clean()
        
        # Ensure organization is set
        if hasattr(order, 'organization'):
            invoice.organization = order.organization  # Ensure `order` has an `organization` attribute

        invoice.save()
        if language_code is not None:
            translation.deactivate()

    def send_invoice_by_email(self):
        if self.type in getattr(
            settings, 'PLANS_SEND_EMAILS_DISABLED_INVOICE_TYPES', []
        ):
            return

        language_code = get_user_language(self.user)

        if language_code is not None:
            translation.activate(language_code)
        mail_context = {
            'user': self.user,
            'invoice_type': self.get_type_display(),
            'invoice_number': self.get_full_number(),
            'order': self.order.id,
            'order_object': self.order,
            'url': self.get_absolute_url(),
        }
        if language_code is not None:
            translation.deactivate()
        send_template_email(
            [self.user.email],
            'gmtisp_billing/mail/invoice_created_title.txt',
            'gmtisp_billing/mail/invoice_created_body.txt',
            mail_context,
            language_code,
        )

    def is_UE_customer(self):
        return EUTaxationPolicy.is_in_EU(self.buyer_country.code)


# ----------------------------------------------------------- payments
from ..signals import status_changed
# from payments.core import get_base_url

class AbstractPayment(OrgMixin, BaseMixin):

    PAYMENT_METHOD_CHOICES = (
        ('momo', _('Mobile Money (MoMo)')),
        ('cash', _('Cash')),
        ('credit_card', _('Credit Card')),
    )
    PAYMENT_ACTION_CHOICES = (
        ('online', _('Online')),
        ('offline', _('Back Office')),
    )

    WAITING = "waiting"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"

    PAYMENT_STATUS_CHOICES = [
        (WAITING, pgettext_lazy("payment status", "Waiting for confirmation")),
        (CONFIRMED, pgettext_lazy("payment status", "Confirmed")),
        (FAILED, pgettext_lazy("payment status", "Failed")),
        (REFUNDED, pgettext_lazy("payment status", "Refunded")),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'), on_delete=models.CASCADE)
    order = models.ForeignKey('gmtisp_billing.Order', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_('order'))
    amount = models.DecimalField(_('amount'), max_digits=MAX_LENGTH, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='GHS')
    method = models.CharField(_('payment method'), max_length=MAX_LENGTH, choices=PAYMENT_METHOD_CHOICES)
    action = models.CharField(_('payment action'), max_length=MAX_LENGTH, choices=PAYMENT_ACTION_CHOICES, default='offline')
    status = models.CharField(_('status'), max_length=MAX_LENGTH, choices=PAYMENT_STATUS_CHOICES, default=WAITING)
    transaction_ref = models.CharField(_('transaction ID'), max_length=255, blank=True, null=True)
    payment_date = models.DateTimeField(_('payment date'), default=timezone.now)
    customer_ip_address = models.GenericIPAddressField(blank=True, null=True)
    delivery = models.DecimalField(max_digits=9, decimal_places=2, default="0.0")
    autorenewed_payment = models.BooleanField(default=False)
    user_message = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["status", "transaction_ref"]),
        ]
        abstract = True
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ('-created',)

    def __str__(self):
        return f'Payment {self.id} - {self.user} - {self.amount} {self.currency}'
        
    def is_successful(self):
        return self.status == self.CONFIRMED

    def is_pending(self):
        return self.status == self.WAITING

    def is_failed(self):
        return self.status == self.FAILED

    def is_refunded(self):
        return self.status == self.REFUNDED

    def refund_payment(self):
        """Refund the payment if it's confirmed."""
        if self.status == self.CONFIRMED:
            self.status = self.REFUNDED
            self.save()

    def update_user_plan(self):
        """Handle user plan updates after successful payment."""
        UserPlan = AbstractUserPlan.get_concrete_model()
        try:
            user_plan = UserPlan.objects.get(user=self.user)
            user_plan.extend_plan()  # Example method to extend plan duration
            user_plan.save()
            account_change_plan.send(sender=self.__class__, user=self.user)
        except UserPlan.DoesNotExist:
            pass  # Handle if user has no plan or other logic

    def check_plan_quota(self):
        """Check and validate quotas related to user's plan after payment."""
        plan_validation(self.user, on_activation=False)

    def save(self, *args, **kwargs):
        """Override save method to handle updates and signals."""
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new and self.is_successful():
            self.process_payment()

    def get_failure_url(self):
        return reverse("order_payment_failure", kwargs={"pk": self.order.pk})

    def get_success_url(self):
        return reverse("order_payment_success", kwargs={"pk": self.order.pk})

    def get_payment_url(self):
        return reverse("payment_details", kwargs={"payment_id": self.pk})

    def delete(self, *args, **kwargs):
        """Handle deletion of payments."""
        if self.status == self.CONFIRMED:
            self.refund_payment()
        super().delete(*args, **kwargs)

@receiver(account_automatic_renewal)
def renew_accounts(sender, user, *args, **kwargs):
    userplan = user.userplan
    if (
        userplan.recurring.payment_provider in settings.PAYMENT_VARIANTS
        and userplan.recurring.renewal_triggered_by
        == AbstractRecurringUserPlan.RENEWAL_TRIGGERED_BY.TASK
    ):
        order = userplan.recurring.create_renew_order()
        payment = AbstractPayment(
            user=user,
            order=order,
            amount=order.total(),
            currency=order.currency,
            method=userplan.recurring.payment_provider,
            autorenewed_payment=True
        )
        payment.save()
        try:
            redirect_url = payment.auto_complete_recurring()
        except Exception as e:
            logger.exception(
                "Exception during account renewal",
                extra={"payment": payment},
            )
            redirect_url = urljoin(
                get_base_url(),
                reverse("create_order_plan", kwargs={"pk": order.get_plan_quota().pk}),
            )
        if redirect_url != "success":
            send_template_email(
                [payment.order.user.email],
                "gmtisp_billing/mail/renew_cvv_3ds_title.txt",
                "gmtisp_billing/mail/renew_cvv_3ds_body.txt",
                {"redirect_url": redirect_url},
                get_user_language(payment.order.user),
            )
        if payment.status == AbstractPayment.CONFIRMED:
            order.complete_order()

# @receiver(status_changed, sender=AbstractPayment)
# def change_payment_status(sender, *args, **kwargs):
#     payment = kwargs["instance"]
#     order = payment.order
#     if payment.status == payment.CONFIRMED:
#         if hasattr(order.user.userplan, "recurring"):
#             order.user.userplan.recurring.token_verified = True
#             order.user.userplan.recurring.save()
#         order.complete_order()
#     if (
#         getattr(settings, "PLANS_PAYMENTS_RETURN_ORDER_WHEN_PAYMENT_REFUNDED", False)
#         and payment.status == payment.REFUNDED
#     ):
#         order._change_reason = f"Django-plans-payments: Payment status changed to {payment.status}"
#         order.return_order()
#     elif order.status != AbstractOrder.get_concrete_model().STATUS.COMPLETED and payment.status not in (
#         payment.CONFIRMED,
#         payment.WAITING,
#     ):
#         order.status = AbstractOrder.get_concrete_model().STATUS.CANCELED
#         order._change_reason = f"Django-plans-payments: Payment status changed to {payment.status}"
#         order.save()
#         if hasattr(order.user.userplan, "recurring"):
#             order.user.userplan.recurring.token_verified = False
#             order.user.userplan.recurring.save()

def get_client_ip(request):
    return request.META.get("REMOTE_ADDR")
