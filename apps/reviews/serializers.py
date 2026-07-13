from rest_framework import serializers

from apps.orders.models import Order, OrderStatus
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source="customer.username", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id", "customer", "customer_username", "order", "food_item", "restaurant",
            "rating", "comment", "created_at", "updated_at",
        )
        read_only_fields = ("id", "customer", "created_at", "updated_at")

    def validate_rating(self, value):
        # Validation rule: ratings must be between 1 and 5.
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        if not attrs.get("food_item") and not attrs.get("restaurant"):
            raise serializers.ValidationError(
                "A review must target either a food item or a restaurant."
            )

        order = attrs.get("order")
        request = self.context.get("request")
        if order and request and order.customer_id != request.user.id:
            raise serializers.ValidationError({"order": "This order does not belong to you."})
        if order and order.status != OrderStatus.DELIVERED:
            raise serializers.ValidationError(
                {"order": "You can only review items from a delivered order."}
            )
        return attrs
