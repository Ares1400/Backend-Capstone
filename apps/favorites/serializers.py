from rest_framework import serializers

from .models import Favorite


class FavoriteSerializer(serializers.ModelSerializer):
    food_item_name = serializers.CharField(source="food_item.name", read_only=True, default=None)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True, default=None)

    class Meta:
        model = Favorite
        fields = ("id", "user", "food_item", "food_item_name", "restaurant", "restaurant_name", "created_at")
        read_only_fields = ("id", "user", "created_at")

    def validate(self, attrs):
        if not attrs.get("food_item") and not attrs.get("restaurant"):
            raise serializers.ValidationError("Specify either a food_item or a restaurant to favorite.")
        if attrs.get("food_item") and attrs.get("restaurant"):
            raise serializers.ValidationError("Favorite either a food_item or a restaurant, not both at once.")
        return attrs
