"""
Order views.

Covers spec section 4.6 endpoints:
    POST   /api/orders/             -> place order (checkout from cart)
    GET    /api/orders/             -> list orders (scoped by role)
    GET    /api/orders/{id}/        -> order detail
    PATCH  /api/orders/{id}/status/ -> update order status (lifecycle)
"""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart
from apps.core.permissions import IsCustomer, IsAdmin
from apps.core.responses import success_response
from .models import Order, OrderItem, OrderStatus
from .serializers import OrderSerializer, CheckoutSerializer, OrderStatusUpdateSerializer

# Flat delivery fee for simplicity; a real system would compute this from
# distance. Kept as a module constant so it's easy to find/change.
DELIVERY_FEE = 500.00


class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/orders/  -> orders scoped to the requester's role:
                           customers see their own; restaurant owners see
                           orders placed at their restaurant(s); admins see all.
    POST /api/orders/  -> checkout: converts the customer's cart into an Order.
    """

    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "restaurant"]
    ordering_fields = ["created_at", "total"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsCustomer()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.select_related("customer", "restaurant").prefetch_related("items")
        if user.is_staff or user.role == "admin":
            return qs
        if user.role == "restaurant_owner":
            return qs.filter(restaurant__owner=user)
        return qs.filter(customer=user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart = get_object_or_404(Cart, user=request.user)
        cart_items = list(cart.items.select_related("food_item", "food_item__restaurant"))

        # Validation rule: orders must have at least one item.
        if not cart_items:
            return Response(
                {"success": False, "message": "Your cart is empty. Add items before checking out."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enforce single-restaurant checkout per order (spec lists
        # "Multi-restaurant checkout" only as an advanced bonus feature;
        # core scope assumes one restaurant per order).
        restaurant_ids = {item.food_item.restaurant_id for item in cart_items}
        if len(restaurant_ids) > 1:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Your cart contains items from multiple restaurants. "
                        "Please order from one restaurant at a time."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        for item in cart_items:
            if not item.food_item.is_available:
                return Response(
                    {"success": False, "message": f"'{item.food_item.name}' is no longer available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        order = Order.objects.create(
            customer=request.user,
            restaurant=cart_items[0].food_item.restaurant,
            delivery_address=data["delivery_address"],
            delivery_phone=data["delivery_phone"],
            notes=data.get("notes", ""),
            delivery_fee=DELIVERY_FEE,
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                food_item=item.food_item,
                food_name=item.food_item.name,
                unit_price=item.food_item.effective_price,
                quantity=item.quantity,
            )

        order.recalculate_totals()
        cart_items_qs = cart.items.all()
        cart_items_qs.delete()  # clear the cart after successful checkout

        return success_response(
            message="Order placed successfully.",
            data=OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/orders/{id}/ — order detail, scoped to owner/restaurant/admin."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.select_related("customer", "restaurant").prefetch_related("items")
        if user.is_staff or user.role == "admin":
            return qs
        if user.role == "restaurant_owner":
            return qs.filter(restaurant__owner=user)
        return qs.filter(customer=user)


class OrderStatusUpdateView(APIView):
    """
    PATCH /api/orders/{id}/status/ — advance the order through its lifecycle.

    Only the restaurant owner (for their own orders) or an admin can change
    status, except for cancellation, which the customer may also trigger
    while the order is still pending.
    """

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        order = get_object_or_404(Order, id=id)
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        user = request.user
        is_owner_of_restaurant = order.restaurant.owner_id == user.id
        is_admin = user.is_staff or user.role == "admin"
        is_customer_cancelling = (
            order.customer_id == user.id and new_status == OrderStatus.CANCELLED
        )

        if not (is_owner_of_restaurant or is_admin or is_customer_cancelling):
            return Response(
                {"success": False, "message": "You do not have permission to update this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not order.can_transition_to(new_status):
            return Response(
                {
                    "success": False,
                    "message": f"Cannot transition order from '{order.status}' to '{new_status}'.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        order.save()
        return success_response(
            message=f"Order status updated to '{new_status}'.",
            data=OrderSerializer(order).data,
        )
