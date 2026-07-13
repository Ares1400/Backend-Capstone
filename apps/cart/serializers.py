from rest_framework import serializers

from apps.menu.models import FoodItem
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    food_item_name = serializers.CharField(source="food_item.name", read_only=True)
    food_item_price = serializers.DecimalField(
        source="food_item.effective_price", max_digits=10, decimal_places=2, read_only=True
    )
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = (
            "id", "food_item", "food_item_name", "food_item_price",
            "quantity", "subtotal", "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate_quantity(self, value):
        # Validation rule: quantity must be greater than 0.
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def validate_food_item(self, food_item):
        if not food_item.is_available:
            raise serializers.ValidationError("This food item is currently unavailable.")
        return food_item


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "user", "items", "total", "total_items", "updated_at")
        read_only_fields = fields
