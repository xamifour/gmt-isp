# myapp/templatetags/sidebar_links.py

from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.inclusion_tag('partials/sidebar_links.html', takes_context=True)
def get_sidebar_links(context):
    request = context['request']
    links = [
        # {
        #     'name': 'Dashboard',
        #     'url_name': 'index',
        #     'icon': 'fas fa-home',
        # },
        {
            'name': 'Users & Organizations',
            'icon': 'fas fa-users',
            'children': [
                {'name': 'Users', 'url_name': 'user_list', 'icon': 'flaticon-users'},
                {'name': 'Organizations', 'url_name': 'organization_list', 'icon': 'flaticon-technology-1'},
            ],
        },
        # {
        #     'name': 'Plans',
        #     'icon': 'fas fa-layer-group',
        #     'children': [
        #         {'name': 'Plans List', 'url_name': 'plans_list', 'icon': 'fas fa-list'},
        #         {'name': 'Pricing', 'url_name': 'pricing', 'icon': 'fas fa-tag'},
        #         {'name': 'Current Plan', 'url_name': 'current_plan', 'icon': 'fas fa-check'},
        #         {'name': 'Upgrade Plan', 'url_name': 'upgrade_plan', 'icon': 'fas fa-arrow-up'},
        #         {'name': 'Change Plan', 'url_name': 'change_plan', 'icon': 'fas fa-exchange-alt'},
        #     ],
        # },
        # {
        #     'name': 'Orders',
        #     'icon': 'fas fa-shopping-cart',
        #     'children': [
        #         {'name': 'Create Order Plan', 'url_name': 'create_order_plan', 'icon': 'fas fa-plus'},
        #         {'name': 'Upgrade Order Plan', 'url_name': 'create_order_plan_change', 'icon': 'fas fa-arrow-up'},
        #         {'name': 'Order Details', 'url_name': 'order_detail', 'icon': 'fas fa-info'},
        #         {'name': 'Order List', 'url_name': 'order_list', 'icon': 'flaticon-cart'},
        #         {'name': 'Order Payment Return', 'url_name': 'order_payment_return', 'icon': 'fas fa-undo'},
        #     ],
        # },
        {
            'name': 'Billing',
            'icon': 'fas fa-file-invoice-dollar',
            'children': [
                {'name': 'Plans', 'url_name': 'plans_list', 'icon': 'flaticon-layers-1'},
                {'name': 'Current Plan', 'url_name': 'current_plan', 'icon': 'flaticon-layers'},
                {'name': 'Orders', 'url_name': 'order_list', 'icon': 'flaticon-cart'},
                {'name': 'Order Return', 'url_name': 'order_payment_return', 'icon': 'flaticon-back'},
                {'name': 'Invoices', 'url_name': 'invoice_list', 'icon': 'flaticon-credit-card-1'},
                {'name': 'Payments', 'url_name': 'payment_list', 'icon': 'flaticon-coins'},
            ],
        },
        # {
        #     'name': 'Invoices',
        #     'icon': 'fas fa-file-invoice',
        #     'children': [
        #         {'name': 'Invoice List', 'url_name': 'invoice_list', 'icon': 'flaticon-credit-card-1'},
        #         {'name': 'Invoice Create', 'url_name': 'invoice_detail', 'icon': 'fas fa-info-circle'},
        #     ],
        # },
        # {
        #     'name': 'Payments',
        #     'icon': 'fas fa-credit-card',
        #     'children': [
        #         {'name': 'Payment List', 'url_name': 'payment_list', 'icon': 'flaticon-coins'},
        #         {'name': 'Create Payment', 'url_name': 'payment_create', 'icon': 'fas fa-plus'},
        #     ],
        # },
    ]

    for item in links:
        if 'children' in item:
            for child in item['children']:
                try:
                    url = reverse(child['url_name'])
                    active = 'active' if request.path == url else ''
                    child['url'] = url
                    child['active'] = active
                except NoReverseMatch:
                    child['url'] = '#'
                    child['active'] = ''
        else:
            try:
                url = reverse(item['url_name'])
                active = 'active' if request.path == url else ''
                item['url'] = url
                item['active'] = active
            except NoReverseMatch:
                item['url'] = '#'
                item['active'] = ''

    return {'links': links}
