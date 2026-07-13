"""
Payment tests — covers spec section 11 "Payment tests".

Paystack's actual HTTP calls are mocked so the suite runs fully offline
and deterministically (no real network call, no dependency on a live
test API key being present in CI).
"""

from unittest.mock import patch

from rest_framework import status

from .helpers import BaseAPITestCase
from apps.orders.models import Order
from apps.payments.models import Payment, PaymentStatus


class CashOnDeliveryPaymentTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.order = Order.objects.create(
            customer=self.customer, restaurant=self.restaurant,
            delivery_address="X", delivery_phone="0800", total="2500.00",
        )

    def test_initiate_cash_payment(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/payments/", {"order": self.order.id, "method": "cash"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["status"], "pending")
        self.assertEqual(response.data["data"]["method"], "cash")

    def test_cannot_create_duplicate_payment_for_same_order(self):
        self.auth_as(self.customer)
        self.client.post("/api/payments/", {"order": self.order.id, "method": "cash"})
        response = self.client.post("/api/payments/", {"order": self.order.id, "method": "cash"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PaystackPaymentTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.order = Order.objects.create(
            customer=self.customer, restaurant=self.restaurant,
            delivery_address="X", delivery_phone="0800", total="2500.00",
        )

    @patch("apps.payments.views.initialize_transaction")
    def test_initiate_paystack_payment_success(self, mock_init):
        mock_init.return_value = {
            "authorization_url": "https://checkout.paystack.com/abc123",
            "access_code": "abc123",
        }
        self.auth_as(self.customer)
        response = self.client.post("/api/payments/", {"order": self.order.id, "method": "paystack"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("checkout.paystack.com", response.data["data"]["paystack_authorization_url"])

    @patch("apps.payments.views.initialize_transaction")
    def test_initiate_paystack_payment_handles_provider_error(self, mock_init):
        from apps.payments.services import PaystackError
        mock_init.side_effect = PaystackError("Invalid key")

        self.auth_as(self.customer)
        response = self.client.post("/api/payments/", {"order": self.order.id, "method": "paystack"})
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    @patch("apps.payments.views.verify_transaction")
    def test_verify_payment_marks_successful(self, mock_verify):
        mock_verify.return_value = {"status": "success"}

        payment = Payment.objects.create(
            order=self.order, customer=self.customer, method="paystack", amount="2500.00",
        )
        self.auth_as(self.customer)
        response = self.client.post("/api/payments/verify/", {"reference": str(payment.reference)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.SUCCESSFUL)
