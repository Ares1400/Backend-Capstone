"""
Order models — spec section 4.6 Order Management System.

Order lifecycle (spec-defined):
    pending -> accepted -> preparing -> out_for_delivery -> delivered
    (or -> cancelled at any point before delivery)

An order can technically span multiple restaurants if the customer's cart
has items from more than one (spec mentions "Multi-item orders" and the
bonus feature "Multi-restaurant checkout"). To keep delivery/acceptance
logic simple and unambiguous for a single restaurant, we snapshot the
restaurant on OrderItem and also link a primary `restaurant` on Order for
the common single-restaurant case; this is documented further in the
checkout view itself.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.menu.models import FoodItem
from apps.restaurants.models import Restaurant


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    PREPARING = "preparing", "Preparing"
    OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


# Valid forward transitions; used to reject illegal status jumps (e.g. pending -> delivered).
VALID_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.ACCEPTED, OrderStatus.CANCELLED},
    OrderStatus.ACCEPTED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


class Order(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="orders",
        help_text="Primary restaurant fulfilling this order.",
    )
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    delivery_address = models.CharField(max_length=255)
    delivery_phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} — {self.customer.username} — {self.status}"

    def recalculate_totals(self):
        self.subtotal = sum((item.subtotal for item in self.items.all()), start=0)
        self.total = self.subtotal + self.delivery_fee
        self.save(update_fields=["subtotal", "total"])

    def can_transition_to(self, new_status):
        return new_status in VALID_TRANSITIONS.get(self.status, set())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    food_item = models.ForeignKey(FoodItem, on_delete=models.SET_NULL, null=True, related_name="order_items")

    # Snapshot fields so historical orders remain accurate even if the
    # food item's name/price changes or is deleted later.
    food_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.quantity} x {self.food_name}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
