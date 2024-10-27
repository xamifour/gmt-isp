import json
import requests
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from .models import Order, Payment
from usermanager.tasks import create_user_profile_in_mikrotik

logger = logging.getLogger(__name__)

def initiate_payment(request, order_id=None):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    order = get_object_or_404(Order, pk=order_id, user=request.user)

    # Retrieve organization for the user
    try:
        from django.core.exceptions import ObjectDoesNotExist
        OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
        organization_user = OrganizationUser.objects.get(user=request.user)
        organization = organization_user.organization
    except ObjectDoesNotExist:
        organization = None
        logger.warning("OrganizationUser not found for the current user.")

    # Create a payment object
    payment = Payment.objects.create(
        user=request.user,
        order=order,
        organization=organization,
        amount=order.total(),
        method='Paystack',
    )

    payment_data = {
        "email": request.user.email,
        "amount": int(order.total() * 100),  # Convert amount to kobo
        "reference": payment.transaction_id,  # Use the transaction ID from the Payment object
        "callback_url": request.build_absolute_uri(reverse('verify_payment'))
    }

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    # Send request to Paystack to initialize payment
    response = requests.post('https://api.paystack.co/transaction/initialize', json=payment_data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        payment_url = response_data['data']['authorization_url']
        return redirect(payment_url)
    else:
        payment.delete()  # Clean up if initiation fails
        return JsonResponse({'error': 'Payment initiation failed'}, status=500)


def verify_payment(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    reference = request.GET.get('reference')
    if not reference:
        return JsonResponse({'error': 'Reference is required'}, status=400)

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Verify the payment via Paystack API
        response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('data', {}).get('status') == 'success':
            order_id = reference.split('-')[1]  # Adjust to extract order_id correctly
            order = get_object_or_404(Order, pk=order_id, user=request.user)

            payment = get_object_or_404(Payment, transaction_id=reference)
            payment.order = order
            payment.status = PaymentStatus.CONFIRMED
            payment.save()

            # Trigger any necessary post-payment processes
            create_user_profile_in_mikrotik.delay(order.user.id)

            return redirect('payment_success')
        else:
            logger.warning(f"Payment verification failed for reference: {reference}. Status: {response_data.get('data', {}).get('status')}")
            payment = get_object_or_404(Payment, transaction_id=reference)
            payment.status = "failed"
            payment.save()
            return redirect('payment_failed')

    except requests.RequestException as e:
        logger.error(f"Error verifying payment with Paystack: {e}", exc_info=True)
        return JsonResponse({'error': 'Payment verification failed'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)


@csrf_exempt
def paystack_webhook_view(request):
    if request.method == 'POST':
        try:
            event_data = json.loads(request.body)
            reference = event_data.get('data', {}).get('reference')

            if not reference:
                return JsonResponse({'error': 'Invalid data'}, status=400)

            payment = get_object_or_404(Payment, transaction_id=reference)

            # Extract payment status from webhook data
            payment_status = event_data.get('data', {}).get('status')

            if payment_status == 'success':
                # Update payment status to confirmed
                payment.status = PaymentStatus.CONFIRMED
                payment.payment_date = now()  # Update payment date to current time
                payment.save()

                # Complete the associated order
                payment.order.complete_order()  # Assuming you have a related order
                # Optionally trigger additional tasks
                create_user_profile_in_mikrotik.delay(payment.user.id)

                return JsonResponse({'status': 'success'}, status=200)
            else:
                # Mark payment as failed if not successful
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
