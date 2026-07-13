"""
Routes mounted at /api/admin/ in config/urls.py.

Combines:
    - Restaurant approval workflow (defined in apps.restaurants.urls as
      `admin_urlpatterns`, since those views live in the restaurants app)
    - Platform-wide analytics
    - User management (list/suspend/activate)
"""

from django.urls import path

from apps.restaurants.urls import admin_urlpatterns as restaurant_admin_urlpatterns
from .views import (
    RestaurantAnalyticsView,
    AdminAnalyticsView,
    AdminUserListView,
    AdminSuspendUserView,
    AdminActivateUserView,
)

urlpatterns = [
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<int:id>/suspend/", AdminSuspendUserView.as_view(), name="admin-user-suspend"),
    path("users/<int:id>/activate/", AdminActivateUserView.as_view(), name="admin-user-activate"),
] + restaurant_admin_urlpatterns

# Mounted separately at /api/restaurants/{id}/analytics/ in config/urls.py
restaurant_analytics_urlpatterns = [
    path("<int:id>/analytics/", RestaurantAnalyticsView.as_view(), name="restaurant-analytics"),
]
