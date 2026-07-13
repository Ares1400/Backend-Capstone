"""
Payment views.

Covers spec section 4.7 endpoints:
    POST /api/payments/  -> initiate a payment for an order (Paystack or cash)
    GET  /api/payments/  -> list the customer's payments

Plus a verify endpoint, since Paystack's flow requires a server-side
verification step after the customer completes payment on Paystack's
hosted checkout page (the `authorization_url`).
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsCustomer
from apps.core.responses import success_response
from apps.orders.models import Order
from .models import Payment, PaymentMethod, PaymentStatus
from .serializers import PaymentSerializer, InitiatePaymentSerializer, VerifyPaymentSerializer
from .services import initialize_transaction, verify_transaction, PaystackError


class PaymentListInitiateView(generics.ListAPIView):
    """
    GET  /api/payments/ -> the requester's own payments (or all, for admin).
    POST /api/payments/ -> initiate payment for one of the requester's orders.
    """

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == "admin":
            return Payment.objects.all()
        return Payment.objects.filter(customer=user)

    def post(self, request, *args, **kwargs):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        order = get_object_or_404(Order, id=data["order"], customer=request.user)

        if hasattr(order, "payment"):
            return Response(
                {"success": False, "message": "A payment already exists for this order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = Payment.objects.create(
            order=order,
            customer=request.user,
            method=data["method"],
            amount=order.total,
        )

        if data["method"] == PaymentMethod.CASH:
            # Cash on delivery: stays "pending" until the rider confirms
            # collection (handled in the deliveries app).
            return success_response(
                message="Order placed with Cash on Delivery. Pay the rider on arrival.",
                data=PaymentSerializer(payment).data,
                status=status.HTTP_201_CREATED,
            )

        # Paystack flow: ask Paystack for a hosted checkout link.
        try:
            result = initialize_transaction(
                email=request.user.email,
                amount=float(order.total),
                reference=str(payment.reference),
            )
        except PaystackError as exc:
            payment.status = PaymentStatus.FAILED
            payment.save()
            return Response(
                {"success": False, "message": f"Payment initialization failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment.paystack_authorization_url = result.get("authorization_url", "")
        payment.paystack_access_code = result.get("access_code", "")
        payment.save()

        return success_response(
            message="Payment initialized. Redirect the customer to the authorization URL to pay.",
            data=PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )


class VerifyPaymentView(APIView):
    """
    POST /api/payments/verify/ — confirms with Paystack whether `reference`
    was actually paid, then marks the local Payment record accordingly.
    Call this after the customer is redirected back from Paystack's
    checkout page.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reference = serializer.validated_data["reference"]

        payment = get_object_or_404(Payment, reference=reference)

        try:
            result = verify_transaction(reference)
        except PaystackError as exc:
            return Response(
                {"success": False, "message": f"Verification failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        paystack_status = result.get("status")  # "success", "failed", "abandoned"
        if paystack_status == "success":
            payment.status = PaymentStatus.SUCCESSFUL
            payment.verified_at = timezone.now()
        else:
            payment.status = PaymentStatus.FAILED
        payment.save()

        return success_response(
            message=f"Payment status: {payment.status}.",
            data=PaymentSerializer(payment).data,
        )


class PaymentReceiptView(generics.RetrieveAPIView):
    """GET /api/payments/{id}/receipt/ — simple JSON receipt for a completed payment."""

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == "admin":
            return Payment.objects.all()
        return Payment.objects.filter(customer=user)
