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



'''
This flow ensures that whenever a user tries to exceed their plan's quota (for devices, orders, etc.), 
validation is triggered, and appropriate actions can be taken, such as displaying an error message 
or preventing further actions.
'''
# class DeviceCountValidator(ModelCountValidator):
#     """
#     Validator to check if the user has exceeded the device limit
#     """
#     @property
#     def model(self):
#         return Device  # Replace with the actual model representing the resource

#     @property
#     def code(self):
#         return "device_limit"  # The quota code used in the plan quota

#     def get_queryset(self, user):
#         return self.model.objects.filter(user=user)  # Count the user's devices
    
# def validate_user_plan_quota(user):
#     errors = plan_validation(user)  # This calls all defined validators
#     if errors['required_to_activate']:
#         raise ValidationError(errors['required_to_activate'])

# def check_quota_before_addition(user, add_count=1):
#     quota_dict = get_user_quota(user)  # Fetch the user's current quota
#     validator = DeviceCountValidator()

#     # Call the validator with the quota_dict and the number of items to add
#     validator(user, quota_dict, add=add_count)
