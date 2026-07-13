"""
Core/admin views.

Covers spec section 4.12 Analytics Dashboard:
    Restaurant Analytics: total orders, revenue tracking, best-selling
        foods, order trends.
    Admin Analytics: total users, total restaurants, total orders,
        platform revenue.

Also exposes "Manage users and roles" / "Manage system settings" admin
permissions (3.1) via simple list + suspend endpoints, since the spec
names the permission but doesn't give it its own endpoint table.
"""

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdmin, IsRestaurantOwner
from apps.core.responses import success_response
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.payments.models import Payment, PaymentStatus
from apps.restaurants.models import Restaurant
from apps.users.serializers import UserSerializer

User = get_user_model()


class RestaurantAnalyticsView(APIView):
    """
    GET /api/restaurants/{id}/analytics/ — total orders, revenue, best
    sellers, and a 7-day order trend for one restaurant. Owner or admin only.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        restaurant = get_object_or_404(Restaurant, id=id)
        if restaurant.owner_id != request.user.id and not (
            request.user.is_staff or request.user.role == "admin"
        ):
            return Response(
                {"success": False, "message": "You do not have permission to view this restaurant's analytics."},
                status=403,
            )

        orders = Order.objects.filter(restaurant=restaurant).exclude(status=OrderStatus.CANCELLED)
        total_orders = orders.count()
        total_revenue = orders.aggregate(total=Sum("total"))["total"] or 0

        best_selling = (
            OrderItem.objects.filter(order__restaurant=restaurant)
            .values("food_name")
            .annotate(units_sold=Sum("quantity"))
            .order_by("-units_sold")[:5]
        )

        since = timezone.now() - timedelta(days=7)
        trend_qs = (
            orders.filter(created_at__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        order_trends = {str(row["day"]): row["count"] for row in trend_qs}

        return success_response(
            data={
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "best_selling_foods": list(best_selling),
                "order_trends": order_trends,
            }
        )


class AdminAnalyticsView(APIView):
    """GET /api/admin/analytics/ — platform-wide totals for admins."""

    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        total_users = User.objects.count()
        total_restaurants = Restaurant.objects.count()
        total_orders = Order.objects.exclude(status=OrderStatus.CANCELLED).count()
        platform_revenue = (
            Payment.objects.filter(status=PaymentStatus.SUCCESSFUL).aggregate(total=Sum("amount"))["total"] or 0
        )

        return success_response(
            data={
                "total_users": total_users,
                "total_restaurants": total_restaurants,
                "total_orders": total_orders,
                "platform_revenue": platform_revenue,
            }
        )


class AdminUserListView(generics.ListAPIView):
    """GET /api/admin/users/ — admin view of all platform users."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = User.objects.all()


class AdminSuspendUserView(APIView):
    """PATCH /api/admin/users/{id}/suspend/ — admin deactivates a user account."""

    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, id):
        user = get_object_or_404(User, id=id)
        user.is_active = False
        user.save()
        return success_response(message=f"User '{user.username}' suspended.")


class AdminActivateUserView(APIView):
    """PATCH /api/admin/users/{id}/activate/ — admin reactivates a suspended user account."""

    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, id):
        user = get_object_or_404(User, id=id)
        user.is_active = True
        user.save()
        return success_response(message=f"User '{user.username}' reactivated.")
