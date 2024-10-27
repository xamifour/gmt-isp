from rest_framework import serializers
from django.contrib.auth import get_user_model

from openwisp_utils.api.serializers import ValidatedModelSerializer
from openwisp_users.models import Organization

from gmtisp_billing.models import * 

User = get_user_model()

class PlanSerializer(ValidatedModelSerializer):
    # organization = serializers.PrimaryKeyRelatedField(read_only=True)
    customized = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Plan
        fields = '__all__'
        # fields = [
        #     'id', 'organization', 'name', 'slug', 'description', 'default',
        #     'available', 'visible', 'customized', 'quotas', 'url',
        #     'plan_class', 'plan_type', 'plan_setup_cost', 'rating',
        #     'radius_group', 'temp_radius_group'
        # ]
        read_only_fields = ['id', 'rating', 'customized']

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

class QuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quota
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

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'