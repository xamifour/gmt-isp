from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'plans', PlanViewSet)
router.register(r'billinginfos', BillingInfoViewSet)
router.register(r'userplans', UserPlanViewSet)
router.register(r'recurringuserplans', RecurringUserPlanViewSet)
router.register(r'quotas', QuotaViewSet)
router.register(r'planquotas', PlanQuotaViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]