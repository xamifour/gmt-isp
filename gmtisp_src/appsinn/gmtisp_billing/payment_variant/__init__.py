import json
import requests
import logging
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect

from gmtisp_billing.models import Order, Payment#, PaymentStatus


logger = logging.getLogger(__name__)

class BasePaymentGateway:
    def initiate_payment(self, payment):
        raise NotImplementedError("Subclasses must implement this method.")

    def verify_payment(self, transaction_id):
        raise NotImplementedError("Subclasses must implement this method.")

    def handle_webhook(self, request):
        """
        Default webhook handling method. Can be overridden by subclasses.
        """
        return JsonResponse({'error': 'Method not allowed'}, status=405)


class PaystackGateway(BasePaymentGateway):
    def initiate_payment(self, request, order_id):
        if request.method != 'GET':
            return JsonResponse({'error': 'Method not allowed'}, status=405)

        order = get_object_or_404(Order, pk=order_id, user=request.user)

        # Create a payment object
        payment = Payment.objects.create(
            user=request.user,
            order=order,
            amount=order.total(),
            method='Paystack',
            transaction_id=f"{request.user.id}-{order.id}",  # Generate a unique transaction ID
        )

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": payment.user.email,
            "amount": int(payment.amount * 100),
            "reference": payment.transaction_id,
            "callback_url": payment.get_callback_url(),
        }

        response = requests.post('https://api.paystack.co/transaction/initialize', json=data, headers=headers)
        if response.status_code == 200:
            payment.transaction_id = response.json()['data']['reference']
            payment.save()
            return redirect(response.json()['data']['authorization_url'])
        else:
            payment.delete()  # Clean up if initiation fails
            return JsonResponse({'error': 'Payment initiation failed'}, status=500)

    def verify_payment(self, request):
        if request.method != 'GET':
            return JsonResponse({'error': 'Method not allowed'}, status=405)

        reference = request.GET.get('reference')
        if not reference:
            return JsonResponse({'error': 'Reference is required'}, status=400)

        payment = get_object_or_404(Payment, transaction_id=reference)

        response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers={
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        })

        if response.json()['data']['status'] == 'success':
            payment.status = "confirmed"
            payment.save()
            payment.order.complete_order()  # Assuming you have this method
            return redirect('payment_success')
        else:
            payment.status = "failed"
            payment.save()
            return redirect('payment_failed')

    def handle_webhook(self, request):
        if request.method == 'POST':
            try:
                event_data = json.loads(request.body)
                reference = event_data.get('data', {}).get('reference')

                if not reference:
                    return JsonResponse({'error': 'Invalid data'}, status=400)

                payment = get_object_or_404(Payment, transaction_id=reference)
                payment_status = event_data.get('data', {}).get('status')

                if payment_status == 'success':
                    payment.status = PaymentStatus.CONFIRMED
                    payment.save()
                    payment.order.complete_order()  # Assuming you have this method
                    return JsonResponse({'status': 'success'}, status=200)
                else:
                    payment.status = PaymentStatus.FAILED
                    payment.save()
                    return JsonResponse({'status': 'failed'}, status=200)

            except json.JSONDecodeError:
                logger.error('Invalid payload received', exc_info=True)
                return JsonResponse({'error': 'Invalid payload'}, status=400)
            except Exception as e:
                logger.error(f"Error processing webhook: {e}", exc_info=True)
                return JsonResponse({'error': 'Internal server error'}, status=500)

        return JsonResponse({'error': 'Method not allowed'}, status=405)



class StripeGateway(BasePaymentGateway):
    def initiate_payment(self, payment):
        # Logic to initiate Stripe payment
        pass  # Implement Stripe-specific logic

    def verify_payment(self, transaction_id):
        # Logic to verify Stripe payment
        pass  # Implement Stripe-specific logic

    def handle_webhook(self, request):
        pass