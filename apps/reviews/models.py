"""
Review model — spec section 4.10 Reviews & Ratings.

A single Review can rate a FoodItem, a Restaurant, or both (e.g. "the
jollof was great AND the service was fast"), so both FKs are optional but
at least one must be set — enforced in the serializer, not here, to keep
the model simple and let DRF produce a clean validation error.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.menu.models import FoodItem
from apps.orders.models import Order
from apps.restaurants.models import Restaurant


class Review(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviews",
        help_text="The order this review is based on (ensures only customers who ordered can review).",
    )
    food_item = models.ForeignKey(
        FoodItem, on_delete=models.CASCADE, null=True, blank=True, related_name="reviews"
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, null=True, blank=True, related_name="reviews"
    )

    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        target = self.food_item or self.restaurant
        return f"{self.rating}★ by {self.customer.username} on {target}"
