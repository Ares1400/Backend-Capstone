"""
Read-only serializers for admin/restaurant analytics aggregates.
These don't map to a model; they describe the shape of computed dicts.
"""

from rest_framework import serializers


class RestaurantAnalyticsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    best_selling_foods = serializers.ListField()
    order_trends = serializers.DictField()


class AdminAnalyticsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_restaurants = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    platform_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
