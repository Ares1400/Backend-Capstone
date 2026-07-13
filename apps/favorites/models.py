"""
Favorite model — spec section 4.9 Favorites System.

Like Review, a Favorite can point at a FoodItem or a Restaurant (spec
lists both "Save food items" and "Save restaurants" as features).
"""

from django.conf import settings
from django.db import models

from apps.menu.models import FoodItem
from apps.restaurants.models import Restaurant


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    food_item = models.ForeignKey(
        FoodItem, on_delete=models.CASCADE, null=True, blank=True, related_name="favorited_by"
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, null=True, blank=True, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "food_item"], name="unique_user_food_favorite",
                condition=models.Q(food_item__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["user", "restaurant"], name="unique_user_restaurant_favorite",
                condition=models.Q(restaurant__isnull=False),
            ),
        ]

    def __str__(self):
        target = self.food_item or self.restaurant
        return f"{self.user.username} ♥ {target}"
