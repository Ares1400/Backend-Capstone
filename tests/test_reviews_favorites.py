"""
Reviews & favorites tests — extends CRUD/validation coverage to spec
sections 4.9 and 4.10, including validation rule "Ratings must be
between 1 and 5".
"""

from rest_framework import status

from .helpers import BaseAPITestCase
from apps.orders.models import Order, OrderStatus


class ReviewValidationTests(BaseAPITestCase):
    def test_rating_above_5_rejected(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/reviews/", {
            "food_item": self.food_item.id, "rating": 6, "comment": "Too generous!",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_below_1_rejected(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/reviews/", {
            "food_item": self.food_item.id, "rating": 0, "comment": "Broken scale",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_requires_food_item_or_restaurant(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/reviews/", {"rating": 5, "comment": "Great!"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_review_updates_food_item_average_rating(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/reviews/", {
            "food_item": self.food_item.id, "rating": 5, "comment": "Excellent!",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.food_item.refresh_from_db()
        self.assertEqual(self.food_item.rating, 5.0)
        self.assertEqual(self.food_item.total_reviews, 1)

    def test_cannot_review_order_that_is_not_delivered(self):
        order = Order.objects.create(
            customer=self.customer, restaurant=self.restaurant,
            delivery_address="X", delivery_phone="0800", status=OrderStatus.PENDING,
        )
        self.auth_as(self.customer)
        response = self.client.post("/api/reviews/", {
            "order": order.id, "food_item": self.food_item.id, "rating": 5,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_review_someone_elses_order(self):
        from .helpers import create_user
        other_customer = create_user("otherreviewcustomer", "customer")
        order = Order.objects.create(
            customer=other_customer, restaurant=self.restaurant,
            delivery_address="X", delivery_phone="0800", status=OrderStatus.DELIVERED,
        )
        self.auth_as(self.customer)
        response = self.client.post("/api/reviews/", {
            "order": order.id, "food_item": self.food_item.id, "rating": 5,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FavoriteTests(BaseAPITestCase):
    def test_add_and_remove_favorite_food_item(self):
        self.auth_as(self.customer)

        add_resp = self.client.post("/api/favorites/", {"food_item": self.food_item.id})
        self.assertEqual(add_resp.status_code, status.HTTP_201_CREATED)
        favorite_id = add_resp.data["data"]["id"]

        list_resp = self.client.get("/api/favorites/")
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_resp.data["results"]), 1)

        delete_resp = self.client.delete(f"/api/favorites/{favorite_id}/")
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_cannot_favorite_both_food_item_and_restaurant_at_once(self):
        self.auth_as(self.customer)
        response = self.client.post("/api/favorites/", {
            "food_item": self.food_item.id, "restaurant": self.restaurant.id,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_duplicate_favorite(self):
        self.auth_as(self.customer)
        self.client.post("/api/favorites/", {"food_item": self.food_item.id})
        response = self.client.post("/api/favorites/", {"food_item": self.food_item.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
