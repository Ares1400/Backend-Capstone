from rest_framework import serializers

from .models import Delivery, DeliveryStatus


class DeliverySerializer(serializers.ModelSerializer):
    rider_username = serializers.CharField(source="rider.username", read_only=True, default=None)
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    delivery_address = serializers.CharField(source="order.delivery_address", read_only=True)

    class Meta:
        model = Delivery
        fields = (
            "id", "order", "order_id", "delivery_address", "rider", "rider_username",
            "status", "current_latitude", "current_longitude",
            "assigned_at", "picked_up_at", "delivered_at", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "order_id", "delivery_address", "rider_username",
            "assigned_at", "picked_up_at", "delivered_at", "created_at", "updated_at",
        )


class AssignRiderSerializer(serializers.Serializer):
    rider = serializers.IntegerField(help_text="User ID of the delivery rider to assign.")


class DeliveryStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=DeliveryStatus.choices)
    current_latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    current_longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
