"""
Notification model — spec section 4.11 Notifications System.

In-app notification log (order updates, delivery alerts, payment
confirmations, restaurant notifications). Real push/SMS/email delivery is
out of core scope (would need Celery + a provider — listed as a bonus
feature), but every notification is still recorded here and visible via
the API, and an email is also fired synchronously for the events that
matter most (order placed, payment confirmed) using Django's mail backend.
"""

from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    ORDER_UPDATE = "order_update", "Order Update"
    DELIVERY_ALERT = "delivery_alert", "Delivery Alert"
    PAYMENT_CONFIRMATION = "payment_confirmation", "Payment Confirmation"
    RESTAURANT_NOTICE = "restaurant_notice", "Restaurant Notification"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=30, choices=NotificationType.choices)
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type} -> {self.user.username}: {self.title}"
