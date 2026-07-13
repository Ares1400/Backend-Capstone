from rest_framework import serializers

from .models import Category, FoodItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "created_at")
        read_only_fields = ("id", "slug", "created_at")


class FoodItemSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = FoodItem
        fields = (
            "id", "restaurant", "restaurant_name", "category", "category_name",
            "name", "description", "price", "discount_price", "effective_price",
            "image", "is_available", "preparation_time", "rating", "total_reviews",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "rating", "total_reviews", "created_at", "updated_at")

    def validate_price(self, value):
        # Validation rule: food price cannot be negative.
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_restaurant(self, restaurant):
        # Validation rule: only approved restaurants can publish food items.
        if not restaurant.is_approved:
            raise serializers.ValidationError(
                "This restaurant is not yet approved and cannot publish food items."
            )
        return restaurant

    def validate(self, attrs):
        request = self.context.get("request")
        restaurant = attrs.get("restaurant") or getattr(self.instance, "restaurant", None)
        if request and restaurant and restaurant.owner_id != request.user.id and not request.user.is_staff:
            raise serializers.ValidationError(
                {"restaurant": "You can only add food items to your own restaurant."}
            )
        return attrs
