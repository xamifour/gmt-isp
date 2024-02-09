import logging
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from openwisp_utils.admin_theme.menu import register_menu_group

from swapper import get_model_name

from . import conf as app_settings
logger = logging.getLogger(__name__)


# class PlansConfig(AppConfig):
#     name = "plans"
#     verbose_name = app_settings.APP_VERBOSE_NAME

#     def ready(self):
#         # noinspection PyUnresolvedReferences
#         import plans.listeners  # noqa

class PlansConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plans'
    label = 'plans'
    verbose_name = _('Subscriptions')

    def ready(self):
        self.register_menu_group()

    def register_menu_group(self):
        items = {
            1: {
                'label': _('Plans'),
                'model': get_model_name(self.label, 'Plan'),
                'name': 'changelist',
                'icon': 'ow-radius-accounting',
            },
            2: {
                'label': _('User Plan'),
                'model': get_model_name(self.label, 'UserPlan'),
                'name': 'changelist',
                'icon': 'ow-radius-group',
            },
            3: {
                'label': _('Invoices'),
                'model': get_model_name(self.label, 'Invoice'),
                'name': 'changelist',
                'icon': 'ow-radius-nas',
            },
            4: {
                'label': _('Orders'),
                'model': get_model_name(self.label, 'Order'),
                'name': 'changelist',
                'icon': 'ow-radius-checks',
            },
            5: {
                'label': _('Pricing'),
                'model': get_model_name(self.label, 'Pricing'),
                'name': 'changelist',
                'icon': 'ow-radius-checks',
            },

        }
        register_menu_group(
            position=14,
            config={'label': _('Subscriptions'), 'items': items, 'icon': 'ow-radius'},
        )


# del PlansConfig