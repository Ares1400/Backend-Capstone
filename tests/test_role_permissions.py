"""
Role permission tests — covers spec section 11 "Role permission tests".
"""

from rest_framework import status

from .helpers import BaseAPITestCase, create_user
from apps.restaurants.models import Restaurant, RestaurantStatus


class RestaurantRolePermissionTests(BaseAPITestCase):
    def test_customer_cannot_register_restaurant(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/restaurants/register/", {
            "name": "Customer's Diner",
            "address": "1 Test St",
            "city": "Lagos",
            "phone_number": "08011111111",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_restaurant_owner_can_register_restaurant(self):
        self.auth_as(self.owner)
        response = self.client.post("/api/restaurants/register/", {
            "name": "Owner's New Spot",
            "address": "1 Test St",
            "city": "Lagos",
            "phone_number": "08011111111",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["status"], "pending")

    def test_only_admin_can_approve_restaurant(self):
        pending = Restaurant.objects.create(
            owner=self.owner, name="Pending Place", address="X", city="Lagos",
            phone_number="0800", status=RestaurantStatus.PENDING,
        )

        self.auth_as(self.owner)
        response = self.client.patch(f"/api/admin/restaurants/{pending.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.auth_as(self.admin)
        response = self.client.patch(f"/api/admin/restaurants/{pending.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending.refresh_from_db()
        self.assertEqual(pending.status, RestaurantStatus.APPROVED)

    def test_anonymous_can_browse_approved_restaurants(self):
        response = self.client.get("/api/restaurants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FoodItemRolePermissionTests(BaseAPITestCase):
    def test_only_owner_can_edit_their_food_item(self):
        other_owner = create_user("otherowner", "restaurant_owner")
        self.auth_as(other_owner)
        response = self.client.patch(f"/api/foods/{self.food_item.id}/", {"price": "1.00"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_edit_own_food_item(self):
        self.auth_as(self.owner)
        response = self.client.patch(f"/api/foods/{self.food_item.id}/", {"price": "3000.00"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_create_category_customer_cannot(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/categories/", {"name": "Drinks"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.auth_as(self.admin)
        response = self.client.post("/api/categories/", {"name": "Drinks"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class DeliveryRolePermissionTests(BaseAPITestCase):
    def test_only_delivery_rider_can_update_delivery_status(self):
        from apps.orders.models import Order
        from apps.deliveries.models import Delivery

        order = Order.objects.create(
            customer=self.customer, restaurant=self.restaurant,
            delivery_address="X", delivery_phone="0800",
        )
        delivery = Delivery.objects.create(order=order, rider=self.rider)

        self.auth_as(self.owner)
        response = self.client.patch(f"/api/deliveries/{delivery.id}/status/", {"status": "picked_up"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.auth_as(self.rider)
        response = self.client.patch(f"/api/deliveries/{delivery.id}/status/", {"status": "picked_up"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
