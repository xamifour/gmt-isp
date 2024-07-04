# payment/models.py

import logging
import paystack
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from gmtisp_billing.models import AbstractOrder, AbstractInvoice, OrgMixin

logger = logging.getLogger(__name__)

paystack.api_key = settings.PAYSTACK_SECRET_KEY

class PaystackPayment(OrgMixin, models.Model):
    order = models.OneToOneField(AbstractOrder, on_delete=models.CASCADE, related_name='paystack_payment')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    reference = models.CharField(_('reference'), max_length=100, unique=True)
    status = models.CharField(_('status'), max_length=20, default='pending')
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.status}"

    def verify_payment(self):
        try:
            response = paystack.transaction.verify(self.reference)
            if response['status'] and response['data']['status'] == 'success':
                self.status = 'completed'
                self.order.complete_order()
                self.create_invoice()
                logger.info(f"Payment verified and completed for reference: {self.reference}")
            else:
                self.status = 'failed'
                logger.warning(f"Payment verification failed for reference: {self.reference}")
            self.save()
        except Exception as e:
            self.status = 'error'
            self.save()
            logger.error(f"Error verifying payment for reference: {self.reference} - {str(e)}")
            raise e

    def create_invoice(self):
        try:
            AbstractInvoice.create(self.order, AbstractInvoice.INVOICE_TYPES['INVOICE'])
            logger.info(f"Invoice created for order: {self.order.id}")
        except Exception as e:
            logger.error(f"Error creating invoice for order: {self.order.id} - {str(e)}")


# payment/views.py

import logging
import paystack
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from .models import PaystackPayment
from gmtisp_billing.models import AbstractOrder

logger = logging.getLogger(__name__)

paystack.api_key = settings.PAYSTACK_SECRET_KEY

class InitializePaymentView(View):
    def get(self, request, order_id):
        order = get_object_or_404(AbstractOrder, id=order_id)
        try:
            payment = PaystackPayment.objects.create(
                order=order,
                organization=order.organization,
                amount=order.total(),
                reference=paystack.utils.generate_transaction_reference()
            )
            response = paystack.transaction.initialize(
                reference=payment.reference,
                amount=int(payment.amount * 100),
                email=order.user.email,
                callback_url=request.build_absolute_uri(reverse('payment:callback'))
            )
            # context = {
            #     'order': order,
            #     'payment': payment,
            #     'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,  # Ensure you have this in your settings
            # }
            logger.info(f"Payment initialization successful for reference: {payment.reference}")
            return redirect(response['data']['authorization_url'])
            # return render(request, 'payment/initialize_payment.html', context)
        except Exception as e:
            logger.error(f"Error initializing payment for order {order.id} - {str(e)}")
            return redirect('order:detail', pk=order.id)


# payment/views.py

class PaymentCallbackView(View):
    def get(self, request):
        reference = request.GET.get('reference')
        payment = get_object_or_404(PaystackPayment, reference=reference)
        try:
            payment.verify_payment()
            logger.info(f"Payment callback processed for reference: {reference}")
            return redirect('order:detail', pk=payment.order.pk)
        except Exception as e:
            logger.error(f"Error processing payment callback for reference: {reference} - {str(e)}")
            return redirect('order:detail', pk=payment.order.pk)


# gmtisp_billing/models.py

from django.db import models, transaction
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class AbstractOrder(OrgMixin, BaseMixin):
    # ... existing fields ...

    def complete_order(self):
        # Get locked order to ensure only one completed order is processed at a time
        order = (
            AbstractOrder.get_concrete_model()
            .objects.filter(id=self.id)
            .select_for_update()
            .get()
        )

        if order.completed is None:
            self.plan_extended_from = self.get_plan_extended_from()
            status = self.user.userplan.extend_account(self.plan, self.pricing)
            self.plan_extended_until = self.user.userplan.expire
            order.completed = self.completed = timezone.now()
            if status:
                self.status = self.STATUS.COMPLETED
            else:
                self.status = self.STATUS.NOT_VALID
            self.save()
            order_completed.send(self)
            return True
        else:
            return False

    class Meta:
        ordering = ('-created',)
        abstract = True
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')


# payment/urls.py

from django.urls import path
from .views import InitializePaymentView, PaymentCallbackView

app_name = 'payment'

urlpatterns = [
    path('initialize/<int:order_id>/', InitializePaymentView.as_view(), name='initialize'),
    path('callback/', PaymentCallbackView.as_view(), name='callback'),
]


