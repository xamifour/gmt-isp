from django.conf import settings
from django.urls import path

from .views import (
    AccountActivationView,
    PlanListView,
    BillingInfoCreateOrUpdateView,
    BillingInfoDeleteView,
    ChangePlanView,
    CreateOrderPlanChangeView,
    CreateOrderView,
    CurrentPlanView,
    InvoiceDetailView,
    OrderListView,
    OrderPaymentReturnView,
    OrderView,
    PricingView,
    RedirectToBilling,
    UpgradePlanView,
    FakePaymentsView,
    PaymentListView,
    PaymentDetailView,
    PaymentCreateView,
    PaymentUpdateView,
    PaymentDeleteView,
    # CreatePaymentView, 
    # PaymentDetailView,
)


urlpatterns = [
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Plans
    path('plans~list/', PlanListView.as_view(), name='plans_list'),
    path('account~activation/', AccountActivationView.as_view(), name='account_activation'),
    path('current~plan/', CurrentPlanView.as_view(), name='current_plan'),
    path('upgrade~plan/', UpgradePlanView.as_view(), name='upgrade_plan'),
    path('pricing/', PricingView.as_view(), name='pricing'),
    path('change~plan/', ChangePlanView.as_view(), name='change_plan'),
    path('create~order/', CreateOrderView.as_view(), name='create_order'),
    path('create~order~plan~change/<uuid:pk>/', CreateOrderPlanChangeView.as_view(), name='create_order_plan_change'),
    path('order/<int:pk>/', OrderView.as_view(), name='order_detail'),
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('order~payment~return/<int:pk>/', OrderPaymentReturnView.as_view(), name='order_payment_return'),
    path('billing~info/', BillingInfoCreateOrUpdateView.as_view(), name='billing_info'),
    path('redirect~to~billing/', RedirectToBilling.as_view(), name='redirect_to_billing'),
    path('billing~info~delete/', BillingInfoDeleteView.as_view(), name='billing_info_delete'),
    path('invoice/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ payment

    path('payments/', PaymentListView.as_view(), name='payment_list'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/create/', PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/edit/', PaymentUpdateView.as_view(), name='payment_update'),
    path('payments/<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),

    # path('payment~details/<int:payment_id>/', PaymentDetailView.as_view(),name='payment_details'),
    # path('create~payment/<str:payment_variant>/<int:order_id>/', CreatePaymentView.as_view(), name='create_payment'),

]

if getattr(settings, 'DEBUG', False) or getattr(settings, 'ENABLE_FAKE_PAYMENTS', True):
    urlpatterns += [
        path(
            'fakepayments/<int:pk>/', FakePaymentsView.as_view(), name='fake_payments'
        ),
    ]