"""
Delivery views.

Covers spec section 4.8 endpoints:
    POST  /api/deliveries/             -> create a delivery record + assign a rider
    GET   /api/deliveries/             -> list (scoped by role)
    PATCH /api/deliveries/{id}/status/ -> rider updates delivery status
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsRestaurantOwner, IsDeliveryRider
from apps.core.responses import success_response
from apps.orders.models import Order
from apps.users.models import Role
from django.contrib.auth import get_user_model
from .models import Delivery, DeliveryStatus
from .serializers import DeliverySerializer, AssignRiderSerializer, DeliveryStatusUpdateSerializer

User = get_user_model()


class DeliveryListCreateView(generics.ListAPIView):
    """
    GET  /api/deliveries/ -> deliveries scoped by role (rider sees their
                              assignments, restaurant owner sees their
                              restaurant's deliveries, admin sees all).
    POST /api/deliveries/ -> restaurant owner creates a delivery for one of
                              their orders and assigns a rider.
    """

    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Delivery.objects.select_related("order", "rider")
        if user.is_staff or user.role == "admin":
            return qs
        if user.role == "delivery_rider":
            return qs.filter(rider=user)
        if user.role == "restaurant_owner":
            return qs.filter(order__restaurant__owner=user)
        return qs.filter(order__customer=user)

    def post(self, request, *args, **kwargs):
        if request.user.role not in ("restaurant_owner", "admin") and not request.user.is_staff:
            return Response(
                {"success": False, "message": "Only restaurant owners or admins can assign deliveries."},
                status=status.HTTP_403_FORBIDDEN,
            )

        order_id = request.data.get("order")
        rider_id = request.data.get("rider")
        order = get_object_or_404(Order, id=order_id)

        if order.restaurant.owner_id != request.user.id and not (
            request.user.is_staff or request.user.role == "admin"
        ):
            return Response(
                {"success": False, "message": "You can only assign deliveries for your own restaurant's orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if hasattr(order, "delivery"):
            return Response(
                {"success": False, "message": "A delivery already exists for this order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rider = None
        if rider_id:
            rider = get_object_or_404(User, id=rider_id, role=Role.DELIVERY_RIDER)

        delivery = Delivery.objects.create(
            order=order,
            rider=rider,
            status=DeliveryStatus.ASSIGNED if rider else DeliveryStatus.UNASSIGNED,
            assigned_at=timezone.now() if rider else None,
        )

        return success_response(
            message="Delivery created.",
            data=DeliverySerializer(delivery).data,
            status=status.HTTP_201_CREATED,
        )


class AssignRiderView(APIView):
    """PATCH /api/deliveries/{id}/assign/ — (re)assign a rider to an existing delivery."""

    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]

    def patch(self, request, id):
        delivery = get_object_or_404(Delivery, id=id)
        if delivery.order.restaurant.owner_id != request.user.id:
            return Response(
                {"success": False, "message": "You can only manage deliveries for your own restaurant."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AssignRiderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rider = get_object_or_404(User, id=serializer.validated_data["rider"], role=Role.DELIVERY_RIDER)

        delivery.rider = rider
        delivery.status = DeliveryStatus.ASSIGNED
        delivery.assigned_at = timezone.now()
        delivery.save()

        return success_response(message="Rider assigned.", data=DeliverySerializer(delivery).data)


class DeliveryStatusUpdateView(APIView):
    """PATCH /api/deliveries/{id}/status/ — rider accepts/rejects or advances delivery status."""

    permission_classes = [permissions.IsAuthenticated, IsDeliveryRider]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["status"],
            properties={
                "status": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["accepted", "picked_up", "en_route", "delivered", "rejected"],
                    description="New delivery status"
                ),
                "current_latitude": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Current GPS latitude (optional)"
                ),
                "current_longitude": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Current GPS longitude (optional)"
                ),
            }
        )
    )

    def patch(self, request, id):
        delivery = get_object_or_404(Delivery, id=id, rider=request.user)
        serializer = DeliveryStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        delivery.status = data["status"]
        if "current_latitude" in data:
            delivery.current_latitude = data["current_latitude"]
        if "current_longitude" in data:
            delivery.current_longitude = data["current_longitude"]

        if data["status"] == DeliveryStatus.PICKED_UP:
            delivery.picked_up_at = timezone.now()
        elif data["status"] == DeliveryStatus.DELIVERED:
            delivery.delivered_at = timezone.now()
            delivery.order.status = "delivered"
            delivery.order.save()

        delivery.save()
        return success_response(
            message=f"Delivery status updated to '{delivery.status}'.",
            data=DeliverySerializer(delivery).data,
        )
