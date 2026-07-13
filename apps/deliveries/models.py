"""
Delivery model — spec section 4.8 Delivery System.

Riders are users with role='delivery_rider' (spec 3.4, marked optional
advanced role — included here since "Assign delivery riders" appears as a
core Restaurant Owner permission in 3.2). GPS tracking is listed as
"optional advanced" in the spec, so we store a last-known lat/lng pair
without building live websocket tracking (that's the "Real-time order
tracking (WebSockets)" bonus feature, intentionally out of core scope).
"""

from django.conf import settings
from django.db import models

from apps.orders.models import Order


class DeliveryStatus(models.TextChoices):
    UNASSIGNED = "unassigned", "Unassigned"
    ASSIGNED = "assigned", "Assigned"
    ACCEPTED = "accepted", "Accepted by Rider"
    PICKED_UP = "picked_up", "Picked Up"
    EN_ROUTE = "en_route", "En Route"
    DELIVERED = "delivered", "Delivered"
    REJECTED = "rejected", "Rejected by Rider"


class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery")
    rider = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="deliveries",
    )
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.UNASSIGNED)

    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    assigned_at = models.DateTimeField(blank=True, null=True)
    picked_up_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Deliveries"

    def __str__(self):
        return f"Delivery for Order #{self.order_id} — {self.status}"
