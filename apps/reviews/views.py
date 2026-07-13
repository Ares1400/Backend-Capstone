"""
Review views.

Covers spec section 4.10 endpoints:
    POST /api/reviews/  -> rate a food item and/or restaurant
    GET  /api/reviews/  -> list reviews (filterable by food_item/restaurant)
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions

from apps.core.permissions import IsCustomer
from apps.core.responses import success_response
from .models import Review
from .serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["food_item", "restaurant", "customer"]
    queryset = Review.objects.select_related("customer", "food_item", "restaurant")

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsCustomer()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        return {"request": self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(customer=request.user)
        return success_response(
            message="Review submitted.", data=ReviewSerializer(review).data, status=201
        )


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.select_related("customer", "food_item", "restaurant")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method in ("PUT", "PATCH", "DELETE"):
            if obj.customer_id != request.user.id and not request.user.is_staff:
                self.permission_denied(request, message="You can only modify your own reviews.")
