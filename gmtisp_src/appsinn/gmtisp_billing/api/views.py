from rest_framework import viewsets

from ..models import *
from .serializers import *


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


class BillingInfoViewSet(viewsets.ModelViewSet):
    queryset = BillingInfo.objects.all()
    serializer_class = BillingInfoSerializer


class UserPlanViewSet(viewsets.ModelViewSet):
    queryset = UserPlan.objects.all()
    serializer_class = UserPlanSerializer


class RecurringUserPlanViewSet(viewsets.ModelViewSet):
    queryset = RecurringUserPlan.objects.all()
    serializer_class = RecurringUserPlanSerializer


class PricingViewSet(viewsets.ModelViewSet):
    queryset = Pricing.objects.all()
    serializer_class = PricingSerializer


class QuotaViewSet(viewsets.ModelViewSet):
    queryset = Quota.objects.all()
    serializer_class = QuotaSerializer


class PlanPricingViewSet(viewsets.ModelViewSet):
    queryset = PlanPricing.objects.all()
    serializer_class = PlanPricingSerializer


class PlanQuotaViewSet(viewsets.ModelViewSet):
    queryset = PlanQuota.objects.all()
    serializer_class = PlanQuotaSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
