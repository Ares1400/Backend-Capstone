"""
Separate module purely so config/urls.py can `include()` the restaurant
analytics route under /api/restaurants/ without colliding with the
`urlpatterns` name already used by apps.core.urls (mounted at /api/admin/).
"""

from .urls import restaurant_analytics_urlpatterns as urlpatterns  # noqa: F401
