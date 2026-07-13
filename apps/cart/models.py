"""
Cart models — spec section 4.5 Cart System.

Each customer has exactly one active cart (created lazily) containing
CartItems referencing FoodItem + quantity. Totals are computed properties,
not stored, so they always reflect current food prices.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.menu.models import FoodItem


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total(self):
        return sum((item.subtotal for item in self.items.all()), start=0)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "food_item")

    def __str__(self):
        return f"{self.quantity} x {self.food_item.name}"

    @property
    def subtotal(self):
        return self.food_item.effective_price * self.quantity
