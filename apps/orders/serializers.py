from rest_framework import serializers

from .models import Order, OrderItem, OrderStatus


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "food_item", "food_name", "unit_price", "quantity", "subtotal")
        read_only_fields = ("id", "food_name", "unit_price", "subtotal")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_username = serializers.CharField(source="customer.username", read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "customer", "customer_username", "restaurant", "restaurant_name",
            "status", "delivery_address", "delivery_phone", "notes",
            "subtotal", "delivery_fee", "total", "items", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "customer", "status", "subtotal", "delivery_fee", "total",
            "created_at", "updated_at",
        )


class CheckoutSerializer(serializers.Serializer):
    """
    Input for POST /api/orders/ — checks out the customer's current cart
    into a real Order. Cart must contain at least one item (validation rule).
    """

    delivery_address = serializers.CharField(max_length=255)
    delivery_phone = serializers.CharField(max_length=20)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices)
