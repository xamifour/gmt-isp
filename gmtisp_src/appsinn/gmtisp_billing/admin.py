from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.core.exceptions import ValidationError
from django.db import transaction
from swapper import load_model

from payments import PaymentStatus
from related_admin import RelatedFieldAdmin

from openwisp_users.multitenancy import MultitenantOrgFilter, MultitenantAdminMixin
from openwisp_users.models import Organization
from openwisp_utils.mixins import OrganizationDbAdminMixin
from .signals import account_automatic_renewal
from .models import (
    Plan,
    UserPlan,
    PlanPricing,
    PlanQuota,
    PlanBandwidthSettings,
    Pricing,
    Quota,
    BandwidthSettings, 
    RecurringUserPlan,
    BillingInfo,
    Order,
    Invoice,
    Payment,
)
# from .forms import PlanForm

class UserLinkMixin(object):
    def user_link(self, obj):
        user_model = get_user_model()
        app_label = user_model._meta.app_label
        model_name = user_model._meta.model_name
        change_url = reverse(
            'admin:%s_%s_change' % (app_label, model_name), args=(obj.user.id,)
        )
        return format_html("<a href='{}'>{}</a>", change_url, obj.user.username)

    user_link.short_description = 'User'
    user_link.allow_tags = True


@admin.register(Pricing)
class PricingAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'period',]
    list_display_links = list_display
    exclude = ['organization']


@admin.register(PlanPricing)
class PlanPricingAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.ModelAdmin):
    list_display = ['plan', 'pricing', 'price']
    list_display_links = ['plan', 'price']
    exclude = ['organization']
    

class PlanPricingInline(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.TabularInline):
    model = PlanPricing
    extra = 1
    max_num = 1
    exclude = ['organization'] 


@admin.register(Quota)
class QuotaAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.ModelAdmin):
    list_display = ['codename', 'name', 'description', 'unit', 'is_boolean']
    list_display_links = ['codename', 'name']
    exclude = ['organization']


@admin.register(PlanQuota)
class PlanQuotaAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.ModelAdmin):
    list_display = ['plan', 'quota', 'value', 'organization']
    list_display_links = ['plan', 'quota']
    exclude = ['organization']
    

class PlanQuotaInline(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.TabularInline):
    model   = PlanQuota
    extra   = 1
    max_num = 1
    exclude = ['organization']


@admin.register(BandwidthSettings)
class BandwidthSettingsAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'priority']
    list_display_links =  ['name']
    exclude = ['organization']
    

@admin.register(PlanBandwidthSettings)
class PlanBandwidthSettingsAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.ModelAdmin):
    list_display = ['plan', 'bandwidth', 'organization']
    list_display_links =  list_display
    exclude = ['organization']


class PlanBandwidthSettingsInline(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.StackedInline):
    model   = PlanBandwidthSettings
    extra   = 0
    max_num = 1
    # min_num = 1
    # can_delete = False
    exclude = ['organization']


def copy_plan(modeladmin, request, queryset):
    '''
    Admin command for duplicating plans preserving quotas and pricings.
    '''
    with transaction.atomic():
        for plan in queryset:
            try:
                new_plan = Plan.objects.create(
                    name=f'{plan.name} (Copy)',
                    customized=plan.customized,
                    organization=plan.organization,  # Ensure the organization is copied
                    default=False,
                    available=False,
                )
                for pricing in plan.planpricing_set.all():
                    pricing.pk = None
                    pricing.plan = new_plan
                    pricing.save()

                for quota in plan.planquota_set.all():
                    quota.pk = None
                    quota.plan = new_plan
                    quota.save()

                for bandwidth in plan.planbandwidthsettings_set.all():
                    bandwidth.pk = None
                    bandwidth.plan = new_plan
                    bandwidth.save()

                messages.success(request, _('Plan copied successfully.'))
            except Exception as e:
                messages.error(request, _('Error copying plan: %s') % str(e))

copy_plan.short_description = _('Copy selected plans')

@admin.register(Plan)
class PlanAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.ModelAdmin):
    # form = PlanForm  # Use the custom form
    list_display = [
        'name',
        # 'slug',
        'organization',
        'customized',
        'default',
        'available',
        'is_free',
        'created',
    ]
    search_fields = ('name', 'customized__username', 'customized__email',)
    list_filter = (MultitenantOrgFilter,)
    list_display_links = list_display
    list_select_related = True
    save_on_top = True
    raw_id_fields = ('customized',)
    readonly_fields = ['created', 'modified']
    prepopulated_fields = {'slug': ('name',)}
    inlines = (PlanPricingInline, PlanQuotaInline, PlanBandwidthSettingsInline)
    actions = [copy_plan, 'delete_selected',]
    exclude = ['organization']
        
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'customized', 'plan_setup_cost')
        }),
        (_('Bools'), {
            'fields': ('visible', 'available', 'requires_payment', 'rollover_allowed')
        }),
        (_('Classing'), {
            'fields': ('plan_class', 'plan_type', 'radius_group', 'temp_radius_group', 'default', 'url')
        }),
        (_('Dates'), {
            'fields': ('created', 'modified')
        }),
    )

    def save_model(self, request, obj, form, change):
        # Ensure the organization is set for the plan
        try:
            OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
            organization_user = OrganizationUser.objects.get(user=request.user)
            obj.organization = organization_user.organization
        except OrganizationUser.DoesNotExist:
            raise ValidationError('The user is not associated with any organization.')
        except Exception as e:
            raise ValidationError(f'Error setting organization for the plan: {e}')

        # Check if another plan with the same name exists for the organization
        if Plan.objects.filter(name=obj.name, organization=obj.organization).exclude(pk=obj.pk).exists():
            raise ValidationError(
                f"A plan with the name '{obj.name}' already exists for the organization '{obj.organization}'."
            )
        # Check if another plan with the same slug exists for the organization
        if Plan.objects.filter(slug=obj.slug, organization=obj.organization).exclude(pk=obj.pk).exists():
            raise ValidationError(
                f"A plan with the slug '{obj.slug}' already exists for the organization '{obj.organization}'."
            )
        
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser and obj and obj.default:
            return False
        return super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        if self.get_default_queryset(request, queryset).exists():
            self.message_user(
                request,
                _('Cannot proceed with the delete operation because the batch of items contains the default group, which cannot be deleted.'),
                messages.ERROR
            )
        else:
            super().delete_queryset(request, queryset)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' not in actions:
            actions['delete_selected'] = (admin.actions.delete_selected, 'delete_selected', _('Delete selected %(verbose_name_plural)s'))
        return actions

    def get_default_queryset(self, request, queryset):
        '''Overridable'''
        return queryset.filter(default=True)


class RecurringPlanInline(admin.StackedInline):
    model = RecurringUserPlan
    readonly_fields = ('created', 'modified')
    extra = 0


def autorenew_payment(modeladmin, request, queryset):
    '''
    Automatically renew payment for this plan
    '''
    for user_plan in queryset:
        account_automatic_renewal.send(sender=None, user=user_plan.user)

autorenew_payment.short_description = _('Autorenew plan')


@admin.register(UserPlan)
class UserPlanAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, UserLinkMixin, admin.ModelAdmin):
    list_filter = (
        'active',
        'expire',
        'plan__name',
        'plan__available',
        'plan__visible',
        'recurring__has_automatic_renewal',
        'recurring__payment_provider',
        'recurring__token_verified',
        'recurring__pricing',
    )
    search_fields = ('user__username', 'user__email', 'plan__name', 'recurring__token', 'organization__name')
    list_display = (
        'user',
        'plan',
        'expire',
        'active',
        'recurring__automatic_renewal',
        'recurring__token_verified',
        'recurring__payment_provider',
        'recurring__pricing',
    )
    list_display_links  = list_display
    list_select_related = True
    readonly_fields = ('user_link', 'created', 'modified')
    inlines = (RecurringPlanInline,)
    fields  = ('user', 'user_link', 'plan', 'expire', 'active', 'created', 'modified')
    actions = [autorenew_payment,]
    raw_id_fields = ['user', 'plan', ]

    def recurring__automatic_renewal(self, obj):
        return obj.recurring.has_automatic_renewal

    recurring__automatic_renewal.admin_order_field = 'recurring__has_automatic_renewal'
    recurring__automatic_renewal.boolean = True
    recurring__automatic_renewal.short_description = 'Automatic renewal'

    def recurring__token_verified(self, obj):
        return obj.recurring.token_verified

    recurring__token_verified.admin_order_field = 'recurring__token_verified'
    recurring__token_verified.boolean = True
    recurring__token_verified.short_description = 'Renewal token verified'

    def recurring__payment_provider(self, obj):
        return obj.recurring.payment_provider

    recurring__payment_provider.admin_order_field = 'recurring__payment_provider'
    recurring__payment_provider.short_description = 'Renewal payment_provider'

    def recurring__pricing(self, obj):
        return obj.recurring.pricing

    recurring__automatic_renewal.admin_order_field = 'recurring__pricing'


@admin.register(BillingInfo)
class BillingInfoAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, UserLinkMixin, admin.ModelAdmin):
    list_display = (
        'user',
        'tax_number',
        'name',
        'street',
        'zipcode',
        'city',
        'country',
    )
    search_fields       = ('user__username', 'user__email', 'tax_number', 'name')
    list_display_links  = list_display
    list_select_related = True
    readonly_fields     = ('user_link', 'created', 'modified')
    exclude             = ('user', 'organization')


def make_order_completed(modeladmin, request, queryset):
    for order in queryset:
        order.complete_order()

make_order_completed.short_description = _('Make selected orders completed')


def make_order_invoice(modeladmin, request, queryset):
    for order in queryset:
        if (
            Invoice.objects.filter(
                type=Invoice.INVOICE_TYPES['INVOICE'], order=order
            ).count()
            == 0
        ):
            Invoice.create(order, Invoice.INVOICE_TYPES['INVOICE'])

make_order_invoice.short_description = _('Make invoices for orders')


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0
    raw_id_fields = ('user',)


@admin.register(Order)
class OrderAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.ModelAdmin):
    list_display  = (
        'id',
        'name',
        'created',
        'user',
        'status',
        'completed',
        'tax',
        'amount',
        'currency',
        'plan',
        'pricing',
        'plan_extended_from',
        'plan_extended_until',
    )
    list_filter   = ('status', 'created', 'completed', 'plan__name', 'pricing')
    raw_id_fields = ('user',)
    search_fields = ('id', 'user__username', 'user__email', 'invoice__full_number')
    readonly_fields    = ('created', 'modified')
    list_display_links = list_display
    actions = [make_order_completed, make_order_invoice]
    inlines = (InvoiceInline,)
    exclude = ('organization',)

    def queryset(self, request):
        return (
            super(OrderAdmin, self)
            .queryset(request)
            .select_related('plan', 'pricing', 'user')
        )


@admin.register(Invoice)
class InvoiceAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, admin.ModelAdmin):
    list_display  = (
        'full_number',
        'issued',
        'total_net',
        'currency',
        'user',
        'tax',
        'buyer_name',
        'buyer_city',
        'buyer_tax_number',
    )
    search_fields       = ('full_number', 'buyer_tax_number', 'user__username', 'user__email')
    list_filter         = ('type', 'issued', 'tax', 'currency', 'buyer_country',)
    readonly_fields     = ('created', 'modified')
    list_display_links  = list_display
    list_select_related = True
    raw_id_fields       = ('user', 'order')
    exclude             = ('organization',)



# ---------------------------------------------------------------- Plan payment
class FaultyPaymentsFilter(SimpleListFilter):
    title = 'faulty_payments'
    parameter_name = 'faulty_payments'

    def lookups(self, request, model_admin):
        return [
            ('unconfirmed_order', 'Confirmed payment unconfirmed order'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'unconfirmed_order':
            return queryset.filter(status=PaymentStatus.CONFIRMED).exclude(
                order__status=Order.STATUS.COMPLETED
            )
        return queryset


@admin.register(Payment)
class PaymentAdmin(MultitenantAdminMixin, OrganizationDbAdminMixin, RelatedFieldAdmin):
    list_display = (
        'id',
        'transaction_id',
        'token',
        'order__user',
        'variant',
        'status',
        'fraud_status',
        'currency',
        'total',
        'customer_ip_address',
        'tax',
        'transaction_fee',
        'captured_amount',
        'created',
        'modified',
        'autorenewed_payment',
    )
    list_filter = (
        'status',
        'variant',
        'fraud_status',
        'currency',
        'autorenewed_payment',
        FaultyPaymentsFilter,
    )
    search_fields = (
        'order__user__first_name',
        'order__user__last_name',
        'order__user__email',
        'transaction_id',
        'extra_data',
        'token',
    )
    list_select_related = ('order__user',)
    # autocomplete_fields = ('order',)
    readonly_fields = ('created', 'modified',)
    exclude = ('organization',)
