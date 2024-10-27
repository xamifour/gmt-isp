# payments/providers/paystack/provider.py
import requests
import logging
from django.conf import settings
from payments.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class PaystackProvider(BaseProvider):
    PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
    PAYSTACK_BASE_URL = "https://api.paystack.co"

    def process_data(self, payment, request):
        try:
            webhook_data = request.data
            if webhook_data['status'] == 'success':
                payment.change_status('PAID')
            else:
                payment.change_status('FAILED')
        except Exception as e:
            logger.error(f"Error processing webhook data: {e}")
            # Consider additional error handling here

    def get_form(self, payment, data=None):
        # Render Paystack payment form
        context = {
            'payment': payment,
            'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
            'amount': payment.amount,
            'currency': payment.currency,
            'email': payment.billing_email,
        }
        return render_to_string('payments/paystack/form.html', context)

    def capture(self, payment, amount=None):
        # Paystack does not require capturing as payments are processed immediately
        pass

    def refund(self, payment, amount=None):
        if not amount:
            amount = payment.amount
        
        # Implement refund logic
        response = requests.post(
            f"{self.PAYSTACK_BASE_URL}/refund",
            json={"transaction": payment.transaction_id, "amount": amount * 100},  # Paystack uses kobo
            headers={"Authorization": f"Bearer {self.PAYSTACK_SECRET_KEY}"}
        )
        if response.status_code != 200:
            raise Exception("Refund failed: " + response.json().get('message', 'Unknown error'))
