from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext

from .utils import get_country_code
from .models import Plan, BillingInfo, Order, PlanPricing, Payment



# class PlanForm(forms.ModelForm):
#     class Meta:
#         model = Plan
#         fields = '__all__'  # Use __all__ to include all fields from the model

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         instance = kwargs.get('instance')
#         if instance:  # Edit mode
#             self.fields['name'].widget.attrs['readonly'] = True
#             self.fields['slug'].widget.attrs['readonly'] = True


class OrderForm(forms.Form):
    plan_pricing = forms.ModelChoiceField(
        queryset=PlanPricing.objects.all(), widget=HiddenInput, required=True
    )


class CreateOrderForm(forms.ModelForm):
    """
    This form is intentionally empty as all values for Order object creation need to be computed inside view

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
        fields = ['order', 'amount', 'currency', 'status', 'payment_method']