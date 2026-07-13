from django.urls import path

from .views import DeliveryListCreateView, AssignRiderView, DeliveryStatusUpdateView

urlpatterns = [
    path("", DeliveryListCreateView.as_view(), name="delivery-list-create"),
    path("<int:id>/assign/", AssignRiderView.as_view(), name="delivery-assign"),
    path("<int:id>/status/", DeliveryStatusUpdateView.as_view(), name="delivery-status-update"),
]
