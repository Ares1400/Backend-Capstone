from django.urls import path

from .views import (
    CategoryListCreateView,
    CategoryDetailView,
    FoodItemListCreateView,
    FoodItemDetailView,
)

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path("categories/<int:pk>/", CategoryDetailView.as_view(), name="category-detail"),
    path("foods/", FoodItemListCreateView.as_view(), name="food-list-create"),
    path("foods/<int:pk>/", FoodItemDetailView.as_view(), name="food-detail"),
]
