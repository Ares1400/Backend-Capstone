"""
Favorite views.

Covers spec section 4.9 endpoints:
    POST   /api/favorites/      -> save a food item or restaurant
    GET    /api/favorites/      -> list the user's favorites
    DELETE /api/favorites/{id}/ -> remove a favorite
"""

from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError

from apps.core.responses import success_response
from .models import Favorite
from .serializers import FavoriteSerializer


class FavoriteListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related("food_item", "restaurant")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            favorite = serializer.save(user=request.user)
        except Exception as exc:
            raise ValidationError("This item is already in your favorites.") from exc
        return success_response(
            message="Added to favorites.",
            data=FavoriteSerializer(favorite).data,
            status=status.HTTP_201_CREATED,
        )


class FavoriteDeleteView(generics.DestroyAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Removed from favorites.")
