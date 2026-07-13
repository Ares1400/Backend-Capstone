"""
Menu views.

Covers spec sections 4.3 Menu Categories and 4.4 Food Menu Management:
    GET/POST   /api/categories/
    PUT/DELETE /api/categories/{id}/
    GET/POST   /api/foods/
    GET/PUT/DELETE /api/foods/{id}/
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters

from apps.core.permissions import IsAdmin, IsOwnerOfRestaurant
from .models import Category, FoodItem
from .serializers import CategorySerializer, FoodItemSerializer


class CategoryListCreateView(generics.ListCreateAPIView):
    """GET (public) / POST (admin only) /api/categories/"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.AllowAny()]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET (public) / PUT/DELETE (admin only) /api/categories/{id}/"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.AllowAny()]


class FoodItemListCreateView(generics.ListCreateAPIView):
    """
    GET (public, filterable/searchable) /api/foods/
    POST (restaurant owner only, must own the target restaurant) /api/foods/
    """

    serializer_class = FoodItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["restaurant", "category", "is_available"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "rating", "created_at"]

    def get_queryset(self):
        # Customers only browse available items from approved restaurants by default.
        qs = FoodItem.objects.select_related("restaurant", "category")
        if self.request.query_params.get("all") == "true" and self.request.user.is_authenticated:
            return qs  # owners/admins can pass ?all=true to see everything
        return qs.filter(is_available=True, restaurant__status="approved", restaurant__is_active=True)

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        return {"request": self.request}


class FoodItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET (public) / PUT/PATCH/DELETE (owner or admin) /api/foods/{id}/"""

    queryset = FoodItem.objects.select_related("restaurant", "category")
    serializer_class = FoodItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOfRestaurant]

    def get_serializer_context(self):
        return {"request": self.request}
