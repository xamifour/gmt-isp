from rest_framework import serializers
from django.contrib.auth import get_user_model

from openwisp_radius.models import RadiusGroup
from appsinn.plans.models.plans import * 

User = get_user_model()

class PlanSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    customized = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    quotas = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    radius_group = serializers.PrimaryKeyRelatedField(queryset=RadiusGroup.objects.all(), required=False)
    temp_radius_group = serializers.PrimaryKeyRelatedField(queryset=RadiusGroup.objects.all(), required=False)

    class Meta:
        model = Plan
        fields = [
            'id', 'organization', 'name', 'slug', 'description', 'default',
            'available', 'visible', 'customized', 'quotas', 'url',
            'plan_class', 'plan_type', 'plan_setup_cost', 'rating',
            'radius_group', 'temp_radius_group'
        ]
        read_only_fields = ['id', 'rating']


class BillingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingInfo
        fields = '__all__'

class UserPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPlan
        fields = '__all__'

class RecurringUserPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringUserPlan
        fields = '__all__'

class PricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pricing
        fields = '__all__'

class QuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quota
        fields = '__all__'

class PlanPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanPricing
        fields = '__all__'

class PlanQuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanQuota
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'