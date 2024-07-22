from django.db.models import Case, Count, Sum, When
from django.urls import reverse_lazy
from django.utils.timezone import localdate
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from openwisp_utils.admin_theme import (
    register_dashboard_chart,
    register_dashboard_template,
)

from swapper import get_model_name

from openwisp_utils.admin_theme.menu import register_menu_group, register_menu_subitem
from openwisp_utils.api.apps import ApiAppConfig
from openwisp_utils.utils import register_menu_items


class TestingAppConfig(ApiAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'testing_app'
    label = 'testing_app'
    verbose_name = 'Test App'

    API_ENABLED = True
    REST_FRAMEWORK_SETTINGS = {
        'DEFAULT_THROTTLE_RATES': {'test': '10/minute'},
        'TEST': True,
    }

    def ready(self, *args, **kwargs):
        super().ready(*args, **kwargs)
        self.register_default_menu_items()
        self.register_dashboard_charts()
        self.register_menu_groups()

    def register_default_menu_items(self):
        items = [{'model': 'testing_app.Shelf'}]
        register_menu_items(items)
        # Required only for testing
        register_menu_items(items, name_menu='OPENWISP_TEST_ADMIN_MENU_ITEMS')

    def register_dashboard_charts(self):
        # register_dashboard_chart(
        #     position=0,
        #     config={
        #         'name': _('Nas'),
        #         'query_params': {
        #             'app_label': 'openwisp_radius',
        #             'model': 'nas',
        #             'annotate': {
        #                 'with_nas': Count(
        #                     Case(
        #                         When(
        #                             server__isnull=False,
        #                             then=1,
        #                         )
        #                     )
        #                 ),
        #                 'without_nas': Count(
        #                     Case(
        #                         When(
        #                             server__isnull=True,
        #                             then=1,
        #                         )
        #                     )
        #                 ),
        #             },
        #             'aggregate': {
        #                 'with_nas__sum': Sum('with_nas'),
        #                 'without_nas__sum': Sum('without_nas'),
        #             },
        #         },
        #         'colors': {
        #             'with_nas__sum': '#267126',
        #             'without_nas__sum': '#353c44',
        #         },
        #         'labels': {
        #             # the <strong> is for testing purposes to
        #             # verify it's being HTML escaped correctly
        #             'with_nas__sum': _('<strong>Projects with operators</strong>'),
        #             'without_nas__sum': _('Projects without Nas'),
        #         },
        #         'filters': {
        #             'key': 'with_nas',
        #             'with_nas__sum': 'true',
        #             'without_nas__sum': 'false',
        #         },
        #     },
        # )
        register_dashboard_chart(
            position=21,
            config={
                'name': _('Operator Project Distribution'),
                'query_params': {
                    'app_label': 'testing_app',
                    'model': 'operator',
                    'group_by': 'project__name',
                },
                'colors': {'Utils': 'red', 'User': 'orange'},
                'labels': {'Utils': _('Utils'), 'User': _('User')},
                'quick_link': {
                    'url': reverse_lazy('admin:testing_app_operator_changelist'),
                    'label': 'Open Operators list',
                    'title': 'View complete list of operators',
                    'custom_css_classes': ['negative-top-20'],
                },
            },
        )
        
        # register_dashboard_chart(
        #     position=22,
        #     config={
        #         'name': _('Operator presence in projects'),
        #         'query_params': {
        #             'app_label': 'testing_app',
        #             'model': 'project',
        #             'annotate': {
        #                 'with_operator': Count(
        #                     Case(
        #                         When(
        #                             operator__isnull=False,
        #                             then=1,
        #                         )
        #                     )
        #                 ),
        #                 'without_operator': Count(
        #                     Case(
        #                         When(
        #                             operator__isnull=True,
        #                             then=1,
        #                         )
        #                     )
        #                 ),
        #             },
        #             'aggregate': {
        #                 'with_operator__sum': Sum('with_operator'),
        #                 'without_operator__sum': Sum('without_operator'),
        #             },
        #         },
        #         'colors': {
        #             'with_operator__sum': '#267126',
        #             'without_operator__sum': '#353c44',
        #         },
        #         'labels': {
        #             # the <strong> is for testing purposes to
        #             # verify it's being HTML escaped correctly
        #             'with_operator__sum': _('<strong>Projects with operators</strong>'),
        #             'without_operator__sum': _('Projects without operators'),
        #         },
        #         'filters': {
        #             'key': 'with_operator',
        #             'with_operator__sum': 'true',
        #             'without_operator__sum': 'false',
        #         },
        #     },
        # )
        register_dashboard_chart(
            position=23,
            config={
                'name': _('Shelf Books Type'),
                'query_params': {
                    'app_label': 'testing_app',
                    'model': 'shelf',
                    'group_by': 'books_type',
                },
                'colors': {'HORROR': 'red', 'FANTASY': 'orange'},
                'labels': {'HORROR': _('Horror'), 'FANTASY': _('Fantasy')},
                'main_filters': {
                    'created_at__date': localdate,
                },
            },
        )
        register_dashboard_chart(
            position=24,
            config={
                'name': _('Books'),
                'query_params': {
                    'app_label': 'testing_app',
                    'model': 'book',
                    'group_by': 'author',
                },
                'colors': {'Utils': 'red', 'User': 'orange'},
                # 'colors': {'HORROR': 'red', 'FANTASY': 'orange'},
                'labels': {'HORROR': _('Horror'), 'FANTASY': _('Fantasy')},
                'main_filters': {
                    'created_at__date': localdate,
                },
            },
        )
        register_dashboard_template(
            position=0,
            config={
                'template': 'dashboard_test.html',
                'css': ('dashboard-test.css',),
                'js': ('dashboard-test.js',),
            },
            extra_config={'test_extra_config1': 'dashboard-test.config1'},
        )
        register_dashboard_template(
            position=1,
            config={
                'template': 'dashboard_test.html',
            },
            extra_config={'test_extra_config2': 'dashboard-test.config2'},
            # after_charts=True,
        )

    def register_menu_groups(self):
        auth_config = {
            'label': _('Shelfs'),
            'items': {
                1: {
                    'label': _('Books'),
                    'model': get_model_name(self.label, 'Book'),
                    'name': 'changelist',
                    'icon': 'ow-org',
                },
                2: {
                    'label': _('Shelfs'),
                    'model': get_model_name(self.label, 'Shelf'),
                    'name': 'changelist',
                    'icon': 'ow-permission',
                },
            },
            'icon': 'shelf',
        }
        docs_config = {
            'label': _('Docs'),
            'items': {
                1: {
                    'label': _('OpenWISP'),
                    'url': 'https://openwisp.org/',
                    'icon': 'link',
                }
            },
            'icon': 'docs',
        }
        # register_menu_group(
        #     position=31,
        #     config={
        #         'model': 'testing_app.Shelf',
        #         'name': 'changelist',
        #         'label': _('Shelfs'),
        #         'icon': 'shelf',
        #     },
        # )
        register_menu_group(position=32, config=auth_config)
        register_menu_group(position=33, config=docs_config)
        register_menu_subitem(
            group_position=33,
            item_position=31,
            config={
                'label': _('Code'),
                'url': 'https://openwisp.org/thecode.html',
                'icon': 'code',
            },
        )


del ApiAppConfig
