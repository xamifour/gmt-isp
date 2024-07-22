import logging
from django.apps import AppConfig
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _

from openwisp_utils.admin_theme import register_dashboard_chart
from openwisp_utils.admin_theme.menu import register_menu_group
from swapper import get_model_name

from . import conf as app_settings
logger = logging.getLogger(__name__)


class GmtispBillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gmtisp_billing'
    label = 'gmtisp_billing'
    # verbose_name = _('Subscriptions')
    verbose_name = _(app_settings.APP_VERBOSE_NAME)

    def ready(self, *args, **kwargs):
        # noinspection PyUnresolvedReferences
        import gmtisp_billing.listeners  # noqa
        super().ready(*args, **kwargs)
        self.register_menu_group()
        self.register_dashboard_charts()

    # menu grouping
    def register_menu_group(self):
        items = {
            1: {
                'label': _('Plans'),
                'model': get_model_name(self.label, 'Plan'),
                'name': 'changelist',
                'icon': 'ow-device-group',
            },
            2: {
                'label': _('Orders'),
                'model': get_model_name(self.label, 'Order'),
                'name': 'changelist',
                'icon': 'ow-cer-group',
            },
            3: {
                'label': _('Invoices'),
                'model': get_model_name(self.label, 'Invoice'),
                'name': 'changelist',
                'icon': 'ow-cer-group',
            },
            4: {
                'label': _('Payments'),
                'model': get_model_name(self.label, 'Payment'),
                'name': 'changelist',
                'icon': 'ow-certificate',
            },

        }
        register_menu_group(
            position=13,
            config={'label': _('Subscriptions'), 'items': items, 'icon': 'ow-radius-accounting'},
        )

    # charts on admin dashboard, using positions 9 to 12
    def register_dashboard_charts(self):
        register_dashboard_chart(
            position=9,
            config={
                'name': _('Plans customized'),
                'query_params': {
                    'app_label': 'gmtisp_billing',
                    'model': 'plan',
                    'group_by': 'customized',
                },
                # 'colors': {'HORROR': 'red', 'FANTASY': 'orange'},
                # 'labels': {'HORROR': _('Horror'), 'FANTASY': _('Fantasy')},
                'main_filters': {
                    'created__date': localdate,
                },
            },
        )