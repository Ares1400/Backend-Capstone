"""
Restaurant views.

Covers spec section 4.2 endpoints:
    POST   /api/restaurants/register/
    GET    /api/admin/restaurants/pending/
    PATCH  /api/admin/restaurants/{id}/approve/
    PATCH  /api/admin/restaurants/{id}/reject/

Plus general CRUD/listing for browsing restaurants (implied by
"Browse restaurants" customer permission and "Restaurant profile
management" feature).
"""

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdmin, IsRestaurantOwner, IsOwnerOfRestaurant
from apps.core.responses import success_response
from .models import Restaurant, RestaurantStatus
from .serializers import (
    RestaurantSerializer,
    RestaurantRegisterSerializer,
    RestaurantRejectSerializer,
)


class RestaurantRegisterView(generics.CreateAPIView):
    """POST /api/restaurants/register/ — restaurant owner submits a new restaurant for approval."""

    serializer_class = RestaurantRegisterSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        restaurant = serializer.save()
        return success_response(
            message="Restaurant submitted for approval.",
            data=RestaurantSerializer(restaurant).data,
            status=status.HTTP_201_CREATED,
        )


class RestaurantListView(generics.ListAPIView):
    """
    GET /api/restaurants/ — public browse endpoint. Only approved & active
    restaurants are visible to customers; owners/admins see everything via
    the 'mine' / admin endpoints instead.
    """

    serializer_class = RestaurantSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["city", "state"]
    search_fields = ["name", "city", "description"]
    ordering_fields = ["average_rating", "created_at", "name"]

    def get_queryset(self):
        return Restaurant.objects.filter(status=RestaurantStatus.APPROVED, is_active=True)


class RestaurantDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RestaurantSerializer

    def get_queryset(self):
        qs = Restaurant.objects.all()
        print(f"DEBUG: queryset count = {qs.count()}")
        for r in qs:
            print(f"DEBUG: restaurant id={r.id} name={r.name}")
        return qs

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [permissions.IsAuthenticated(), IsOwnerOfRestaurant()]
        return [permissions.AllowAny()]

class MyRestaurantsView(generics.ListAPIView):
    """GET /api/restaurants/mine/ — restaurant owner's own restaurants, any status."""

    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]

    def get_queryset(self):
        return Restaurant.objects.filter(owner=self.request.user)


class PendingRestaurantsView(generics.ListAPIView):
    """GET /api/admin/restaurants/pending/ — admin view of restaurants awaiting approval."""

    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = Restaurant.objects.filter(status=RestaurantStatus.PENDING)


class ApproveRestaurantView(APIView):
    """PATCH /api/admin/restaurants/{id}/approve/ — admin approves a pending restaurant."""

    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, id):
        restaurant = get_object_or_404(Restaurant, id=id)
        restaurant.status = RestaurantStatus.APPROVED
        restaurant.rejection_reason = ""
        restaurant.save()
        return success_response(
            message=f"Restaurant '{restaurant.name}' approved.",
            data=RestaurantSerializer(restaurant).data,
        )


class RejectRestaurantView(APIView):
    """PATCH /api/admin/restaurants/{id}/reject/ — admin rejects a pending restaurant."""

    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, id):
        restaurant = get_object_or_404(Restaurant, id=id)
        serializer = RestaurantRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        restaurant.status = RestaurantStatus.REJECTED
        restaurant.rejection_reason = serializer.validated_data.get("reason", "")
        restaurant.save()
        return success_response(
            message=f"Restaurant '{restaurant.name}' rejected.",
            data=RestaurantSerializer(restaurant).data,
        )


class SuspendRestaurantView(APIView):
    """PATCH /api/admin/restaurants/{id}/suspend/ — admin suspends an active restaurant."""

    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, id):
        restaurant = get_object_or_404(Restaurant, id=id)
        restaurant.is_active = False
        restaurant.status = RestaurantStatus.SUSPENDED
        restaurant.save()
        return success_response(
            message=f"Restaurant '{restaurant.name}' suspended.",
            data=RestaurantSerializer(restaurant).data,
        )
