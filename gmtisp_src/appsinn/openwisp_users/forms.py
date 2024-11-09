# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from allauth.account.models import EmailAddress
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm, UserChangeForm as BaseUserChangeForm
from .models import User, Organization, OrganizationOwner, OrganizationUser

from django_recaptcha.fields import ReCaptchaField


class RequiredInlineFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        form.empty_permitted = self.instance.is_superuser
        return form

class UserFormMixin(forms.ModelForm):
    email = forms.EmailField(label=_('Email'), max_length=254, required=True)

    # def validate_user_groups(self, data):
    #     is_staff = data.get('is_staff')
    #     is_superuser = data.get('is_superuser')
    #     groups = data.get('groups')
    #     if is_staff and not is_superuser and not groups:
    #         raise ValidationError({'groups': _('A staff user must belong to a group, please select one.')})
    def validate_user_groups(self, data):
        is_staff = data.get('is_staff')
        is_superuser = data.get('is_superuser')
        groups = data.get('groups')
        
        if is_staff and not is_superuser:
            # Check if groups contain any valid IDs
            if not groups or (isinstance(groups, list) and all(g.pk is None for g in groups)):
                raise ValidationError({'groups': _('A staff user must belong to a group, please select one.')})

    def clean(self):
        cleaned_data = super().clean()
        self.validate_user_groups(cleaned_data)
        return cleaned_data

class UserCreationForm(UserFormMixin, BaseUserCreationForm):
    phone_number = PhoneNumberField(widget=forms.TextInput(), required=False)

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone_number', 'birth_date', 'is_active', 'is_staff', 'groups']

class UserChangeForm(UserFormMixin, BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'birth_date', 'is_active', 'is_staff', 'is_superuser', 'groups']

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = '__all__'
        # fields = ['name', 'is_active']

class OrganizationOwnerForm(forms.ModelForm):
    class Meta:
        model = OrganizationOwner
        fields = ['organization_user']

class OrganizationUserForm(forms.ModelForm):
    class Meta:
        model = OrganizationUser
        fields = ['organization', 'is_admin']

# class UserPlanForm(forms.ModelForm):
#     class Meta:
#         model = UserPlan
#         fields = ['organization', 'plan']
