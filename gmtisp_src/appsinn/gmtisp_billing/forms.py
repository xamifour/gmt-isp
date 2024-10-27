from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext

from .utils import get_country_code
from .validators_my import max_plans_validator
from .models import Plan, Order, PlanQuota, BillingInfo, Payment


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        widgets = {'user' : HiddenInput,}
        exclude = ("user",)

    def clean(self):
        cleaned_data = super(PlanForm, self).clean()
        max_plans_validator(cleaned_data['user'], add=1)
        return cleaned_data


class OrderForm(forms.Form):
    plan_quota = forms.ModelChoiceField(
        queryset=PlanQuota.objects.all(), widget=HiddenInput, required=True
    )


class CreateOrderForm(forms.ModelForm):
    """
    This form is intentionally empty as all values for Order object creation need to be 
    computed inside view

    Therefore, when implementing for example a rabat coupons, you can add some fields here
     and create "recalculate" button.
    """

    class Meta:
        model = Order
        fields = tuple()


class BillingInfoForm(forms.ModelForm):
    class Meta:
        model = BillingInfo
        exclude = ("user",)

    def __init__(self, *args, request=None, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        if not self.instance.country:
            self.fields["country"].initial = get_country_code(request)
        return ret_val

    def clean(self):
        cleaned_data = super(BillingInfoForm, self).clean()

        try:
            cleaned_data["tax_number"] = BillingInfo.clean_tax_number(
                cleaned_data["tax_number"], cleaned_data.get("country", None)
            )
        except ValidationError as e:
            self._errors["tax_number"] = e.messages

        return cleaned_data


class BillingInfoWithoutShippingForm(BillingInfoForm):
    class Meta:
        model = BillingInfo
        exclude = (
            "user",
            "shipping_name",
            "shipping_street",
            "shipping_zipcode",
            "shipping_city",
        )


class FakePaymentsForm(forms.Form):
    status = forms.ChoiceField(
        choices=Order.STATUS, required=True, label=gettext("Change order status to")
    )


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['order', 'amount', 'currency', 'status', 'method']
