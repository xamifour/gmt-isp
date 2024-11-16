from django.conf import settings
from django.urls import path

from .views import (
    AccountActivationView,
    PlanListView,
    # BillingInfoCreateOrUpdateView,
    BillingInfoDeleteView,
    ChangePlanView,
    CreateOrderPlanChangeView,
    CreateOrderView,
    CurrentPlanView,
    InvoiceDetailView,
    OrderListView,
    OrderPaymentReturnView,
    OrderView,
    RedirectToBilling,
    UpgradePlanView,
    PaymentListView,
    PlanDetailView,
    PaymentDetailView,
    PaymentUpdateView,
    PaymentDeleteView,
    InvoiceListView,
    payment_success,
    payment_failed,
    paystack_initiate_payment,
    paystack_verify_payment,
    paystack_webhook_view
)


urlpatterns = [
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Plans
    path('account~activation/', AccountActivationView.as_view(), name='account_activation'),

    path('', PlanListView.as_view(), name='plans_list'),
    path('plan~details/<uuid:pk>/', PlanDetailView.as_view(), name='plan_details'),
    path('plan~current/', CurrentPlanView.as_view(), name='current_plan'),
    path('plan~upgrade/', UpgradePlanView.as_view(), name='upgrade_plan'),
    path('plan~change/<uuid:pk>/', ChangePlanView.as_view(), name='change_plan'),

    path('order~extend/<uuid:pk>/', CreateOrderView.as_view(), name='create_order_plan'),
    path('order~upgrade/<uuid:pk>/', CreateOrderPlanChangeView.as_view(), name='create_order_plan_change'),
    path('order~details/<uuid:pk>/', OrderView.as_view(), name='order'),

    path('orders~list/', OrderListView.as_view(), name='order_list'),
    path('order~/<uuid:pk>/payment~success/', OrderPaymentReturnView.as_view(status="success"), name='order_payment_success'),
    path('order~/<uuid:pk>/payment~failure/', OrderPaymentReturnView.as_view(status="failure"), name='order_payment_failure'),
    
    # path('billing~info/', BillingInfoCreateOrUpdateView.as_view(), name='billing_info'),
    path('billing~info/redirect/', RedirectToBilling.as_view(), name='redirect_to_billing'),
    path('billing~info/delete/', BillingInfoDeleteView.as_view(), name='billing_info_delete'),

    path('invoicse~list/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoice~details/<uuid:pk>/', InvoiceDetailView.as_view(), name='invoice_preview_html'),

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ payment
    path('payments~list/', PaymentListView.as_view(), name='payment_list'),
    path('payments~update/<uuid:pk>/', PaymentUpdateView.as_view(), name='payment_update'),
    path('payments~delete/<uuid:pk>/', PaymentDeleteView.as_view(), name='payment_delete'),
    path('payment~details/<uuid:pk>/', PaymentDetailView.as_view(),name='payment_details'),

    path('payment/initiate/<uuid:order_id>/', paystack_initiate_payment, name='initiate_payment'),
    path('verify-payment/', paystack_verify_payment, name='verify_payment'),
    path('payment-success/', payment_success, name='payment_success'),
    path('payment-failed/', payment_failed, name='payment_failed'),
    path('webhook/paystack/', paystack_webhook_view, name='paystack_webhook'),

]