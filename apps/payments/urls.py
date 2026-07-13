from django.urls import path

from .views import PaymentListInitiateView, VerifyPaymentView, PaymentReceiptView

urlpatterns = [
    path("", PaymentListInitiateView.as_view(), name="payment-list-initiate"),
    path("verify/", VerifyPaymentView.as_view(), name="payment-verify"),
    path("<int:pk>/receipt/", PaymentReceiptView.as_view(), name="payment-receipt"),
]
