from rest_framework import serializers

from .models import Restaurant, RestaurantStatus


class RestaurantSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Restaurant
        fields = (
            "id", "owner", "owner_username", "name", "slug", "description", "logo",
            "address", "city", "state", "country", "latitude", "longitude",
            "phone_number", "email", "opening_time", "closing_time", "is_open_now",
            "status", "rejection_reason", "is_active",
            "average_rating", "total_reviews", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "owner", "slug", "status", "rejection_reason",
            "average_rating", "total_reviews", "created_at", "updated_at",
        )


class RestaurantRegisterSerializer(serializers.ModelSerializer):
    """Used at registration time — owner is set from request.user, status defaults to pending."""

    class Meta:
        model = Restaurant
        fields = (
            "id", "name", "description", "logo", "address", "city", "state",
            "country", "latitude", "longitude", "phone_number", "email",
            "opening_time", "closing_time",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        validated_data["status"] = RestaurantStatus.PENDING
        return super().create(validated_data)


class RestaurantRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
