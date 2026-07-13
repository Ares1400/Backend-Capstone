"""
CRUD tests (spec section 11 "CRUD tests") for categories and food items,
plus API response validation tests (the consistent success/error envelope
produced by apps.core.responses / apps.core.exceptions).
"""

from rest_framework import status

from .helpers import BaseAPITestCase
from apps.menu.models import Category, FoodItem


class CategoryCRUDTests(BaseAPITestCase):
    def test_list_categories_is_public(self):
        Category.objects.create(name="Drinks")
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_create_update_delete_category(self):
        self.auth_as(self.admin)

        create_resp = self.client.post("/api/categories/", {"name": "Snacks"})
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        category_id = create_resp.data["id"]

        update_resp = self.client.put(f"/api/categories/{category_id}/", {"name": "Snacks & Sides"})
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        delete_resp = self.client.delete(f"/api/categories/{category_id}/")
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=category_id).exists())


class FoodItemCRUDTests(BaseAPITestCase):
    def test_create_food_item_rejects_negative_price(self):
        self.auth_as(self.owner)
        response = self.client.post("/api/foods/", {
            "restaurant": self.restaurant.id,
            "name": "Suspicious Soup",
            "price": "-10.00",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_food_item_for_unapproved_restaurant_rejected(self):
        from apps.restaurants.models import Restaurant, RestaurantStatus
        unapproved = Restaurant.objects.create(
            owner=self.owner, name="New Place", address="X", city="Lagos",
            phone_number="0800", status=RestaurantStatus.PENDING,
        )
        self.auth_as(self.owner)
        response = self.client.post("/api/foods/", {
            "restaurant": unapproved.id,
            "name": "Too Early Item",
            "price": "1000.00",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_full_food_item_crud_cycle(self):
        self.auth_as(self.owner)

        create_resp = self.client.post("/api/foods/", {
            "restaurant": self.restaurant.id,
            "name": "Suya",
            "price": "1500.00",
        })
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        food_id = create_resp.data["id"]

        get_resp = self.client.get(f"/api/foods/{food_id}/")
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)

        update_resp = self.client.put(f"/api/foods/{food_id}/", {
            "restaurant": self.restaurant.id, "name": "Suya Special", "price": "1800.00",
        })
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        delete_resp = self.client.delete(f"/api/foods/{food_id}/")
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FoodItem.objects.filter(id=food_id).exists())


class ApiResponseShapeTests(BaseAPITestCase):
    """Confirms the consistent {success, message, data/errors} envelope."""

    def test_error_response_has_consistent_envelope(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/cart/", {"food_item": 999999, "quantity": 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("success", response.data)
        self.assertFalse(response.data["success"])
        self.assertIn("errors", response.data)

    def test_success_response_has_consistent_envelope(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/cart/", {"food_item": self.food_item.id, "quantity": 1})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("success", response.data)
        self.assertTrue(response.data["success"])
        self.assertIn("data", response.data)

    def test_unauthenticated_request_returns_401_with_envelope(self):
        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("success", response.data)
        self.assertFalse(response.data["success"])
