from .validators import ModelCountValidator, ModelAttributeValidator
from .models import Plan, PlanQuota, UserPlan


class MaxPlansValidator(ModelCountValidator):
    code = 'MAX_PLAN_COUNT'
    model = UserPlan

    def get_queryset(self, user):
        return super(MaxPlansValidator, self).get_queryset(user).filter(user=user)

max_plans_validator = MaxPlansValidator()


class PlanQuotaValidator(ModelAttributeValidator):
    code = 'MAX_QUOTA_SIZE'
    model = PlanQuota
    attribute = 'value'

    def get_queryset(self, user):
        return super(PlanQuotaValidator, self).get_queryset(user).filter(user=user)

max_quota_validator = PlanQuotaValidator()