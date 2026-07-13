"""
Order flow tests — covers spec section 11 "Order flow tests" and the
order-related entries from "Validation Rules" (section 10).
"""

from rest_framework import status

from .helpers import BaseAPITestCase, create_user
from apps.orders.models import Order, OrderStatus


class CheckoutTests(BaseAPITestCase):
    def test_cannot_checkout_with_empty_cart(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/orders/", {
            "delivery_address": "5 Test Close",
            "delivery_phone": "08099999999",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful_checkout_creates_order_and_clears_cart(self):
        self.auth_as(self.customer)
        self.client.post("/api/cart/", {"food_item": self.food_item.id, "quantity": 2})

        response = self.client.post("/api/orders/", {
            "delivery_address": "5 Test Close",
            "delivery_phone": "08099999999",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["status"], "pending")
        self.assertEqual(len(response.data["data"]["items"]), 1)

        cart_response = self.client.get("/api/cart/")
        self.assertEqual(cart_response.data["data"]["total_items"], 0)

    def test_checkout_rejects_unavailable_food_item(self):
        self.food_item.is_available = False
        self.food_item.save()

        self.auth_as(self.customer)
        # Manually create the cart item since the add-to-cart endpoint also
        # validates availability — we want to test checkout's own check too.
        from apps.cart.models import Cart, CartItem
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, food_item=self.food_item, quantity=1)

        response = self.client.post("/api/orders/", {
            "delivery_address": "5 Test Close",
            "delivery_phone": "08099999999",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderLifecycleTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.order = Order.objects.create(
            customer=self.customer,
            restaurant=self.restaurant,
            delivery_address="5 Test Close",
            delivery_phone="08099999999",
        )

    def test_valid_transition_pending_to_accepted(self):
        self.auth_as(self.owner)
        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "accepted"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_transition_pending_to_delivered_rejected(self):
        self.auth_as(self.owner)
        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "delivered"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_can_cancel_own_pending_order(self):
        self.auth_as(self.customer)
        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cancelled"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_cannot_accept_own_order(self):
        self.auth_as(self.customer)
        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "accepted"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_sees_only_their_own_orders(self):
        other_customer = create_user("othercustomer", "customer")
        Order.objects.create(
            customer=other_customer, restaurant=self.restaurant,
            delivery_address="X", delivery_phone="0800",
        )

        self.auth_as(self.customer)
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [o["id"] for o in response.data["results"]]
        self.assertIn(self.order.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_restaurant_owner_sees_their_restaurants_orders(self):
        self.auth_as(self.owner)
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [o["id"] for o in response.data["results"]]
        self.assertIn(self.order.id, returned_ids)
