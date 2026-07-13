from django.urls import path

from .views import (
    RestaurantRegisterView,
    RestaurantListView,
    RestaurantDetailView,
    MyRestaurantsView,
    PendingRestaurantsView,
    ApproveRestaurantView,
    RejectRestaurantView,
    SuspendRestaurantView,
)

urlpatterns = [
    path("register/", RestaurantRegisterView.as_view(), name="restaurant-register"),
    path("mine/", MyRestaurantsView.as_view(), name="restaurant-mine"),
    path("", RestaurantListView.as_view(), name="restaurant-list"),
    path("<int:pk>/", RestaurantDetailView.as_view(), name="restaurant-detail"),
]

# Admin-only routes — mounted separately under /api/admin/restaurants/ in config/urls.py
admin_urlpatterns = [
    path("restaurants/pending/", PendingRestaurantsView.as_view(), name="restaurant-pending"),
    path("restaurants/<int:id>/approve/", ApproveRestaurantView.as_view(), name="restaurant-approve"),
    path("restaurants/<int:id>/reject/", RejectRestaurantView.as_view(), name="restaurant-reject"),
    path("restaurants/<int:id>/suspend/", SuspendRestaurantView.as_view(), name="restaurant-suspend"),
]
