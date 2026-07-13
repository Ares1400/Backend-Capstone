"""
Auto-generates notifications when key events happen elsewhere in the
system: order status changes and successful payments. Wired up in
NotificationsConfig.ready().
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.orders.models import Order
from apps.payments.models import Payment, PaymentStatus
from .models import NotificationType
from .services import notify


@receiver(post_save, sender=Order)
def notify_on_order_status_change(sender, instance, created, **kwargs):
    if created:
        notify(
            user=instance.customer,
            type=NotificationType.ORDER_UPDATE,
            title="Order placed",
            message=f"Your order #{instance.id} at {instance.restaurant.name} has been placed.",
        )
    else:
        notify(
            user=instance.customer,
            type=NotificationType.ORDER_UPDATE,
            title=f"Order #{instance.id} {instance.get_status_display()}",
            message=f"Your order status is now '{instance.get_status_display()}'.",
        )


@receiver(post_save, sender=Payment)
def notify_on_payment_status_change(sender, instance, created, **kwargs):
    if not created and instance.status == PaymentStatus.SUCCESSFUL:
        notify(
            user=instance.customer,
            type=NotificationType.PAYMENT_CONFIRMATION,
            title="Payment confirmed",
            message=f"Your payment of {instance.amount} for order #{instance.order_id} was successful.",
        )
