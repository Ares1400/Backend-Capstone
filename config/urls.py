"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Restaurant Management & Food Ordering System API",
        default_version="v1",
        description=(
            "API documentation for the Restaurant Management & Food Ordering "
            "System — a Django REST Framework backend supporting restaurant "
            "onboarding, menu management, ordering, payments, delivery "
            "tracking, reviews, and admin analytics."
        ),
        contact=openapi.Contact(email="support@restaurantapp.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # API docs
    path("swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),

    # API v1
    path("api/auth/", include("apps.users.urls")),
    path("api/restaurants/", include("apps.restaurants.urls")),
    path("api/restaurants/", include("apps.core.urls_restaurant_analytics")),
    path("api/", include("apps.menu.urls")),
    path("api/cart/", include("apps.cart.urls")),
    path("api/orders/", include("apps.orders.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/deliveries/", include("apps.deliveries.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/favorites/", include("apps.favorites.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/admin/", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
