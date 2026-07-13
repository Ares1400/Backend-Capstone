"""
Payment model — spec section 4.7 Payment System.

Supports two payment methods:
    - "paystack" : real online payment via Paystack's test-mode API
    - "cash"     : cash on delivery, marked pending until the rider confirms

Receipt generation (spec feature) is implemented as a serializer-level
representation rather than a separate model — see serializers.py.
"""

import uuid

from django.conf import settings
from django.db import models

from apps.orders.models import Order


class PaymentMethod(models.TextChoices):
    PAYSTACK = "paystack", "Paystack (Online)"
    CASH = "cash", "Cash on Delivery"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESSFUL = "successful", "Successful"
    FAILED = "failed", "Failed"


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")

    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Paystack-specific fields
    reference = models.CharField(max_length=100, unique=True, default=uuid.uuid4, editable=False)
    paystack_authorization_url = models.URLField(blank=True)
    paystack_access_code = models.CharField(max_length=100, blank=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment for Order #{self.order_id} — {self.status}"
