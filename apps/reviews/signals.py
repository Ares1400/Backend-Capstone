"""
Signal handlers that keep FoodItem.rating / Restaurant.average_rating in
sync whenever a Review is created, updated, or deleted. Recomputing from
scratch (rather than incrementally) keeps the logic simple and immune to
drift.
"""

from django.db.models import Avg, Count
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Review


def _recalculate_food_item(food_item):
    if food_item is None:
        return
    agg = food_item.reviews.aggregate(avg=Avg("rating"), count=Count("id"))
    food_item.rating = round(agg["avg"] or 0.0, 2)
    food_item.total_reviews = agg["count"] or 0
    food_item.save(update_fields=["rating", "total_reviews"])


def _recalculate_restaurant(restaurant):
    if restaurant is None:
        return
    agg = restaurant.reviews.aggregate(avg=Avg("rating"), count=Count("id"))
    restaurant.average_rating = round(agg["avg"] or 0.0, 2)
    restaurant.total_reviews = agg["count"] or 0
    restaurant.save(update_fields=["average_rating", "total_reviews"])


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_ratings(sender, instance, **kwargs):
    _recalculate_food_item(instance.food_item)
    _recalculate_restaurant(instance.restaurant)
