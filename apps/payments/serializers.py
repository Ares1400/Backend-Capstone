from rest_framework import serializers

from .models import Payment, PaymentMethod


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id", "order", "order_id", "customer", "method", "status", "amount",
            "reference", "paystack_authorization_url", "verified_at",
            "created_at", "updated_at",
        )
        read_only_fields = fields


class InitiatePaymentSerializer(serializers.Serializer):
    order = serializers.IntegerField()
    method = serializers.ChoiceField(choices=PaymentMethod.choices)


class VerifyPaymentSerializer(serializers.Serializer):
    reference = serializers.CharField()
