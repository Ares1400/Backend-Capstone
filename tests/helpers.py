"""
Shared helpers for the test suite: quick factory functions for creating
users of each role, a restaurant, and a food item, so individual test
modules stay short and focused on behavior rather than setup boilerplate.
"""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.menu.models import Category, FoodItem
from apps.restaurants.models import Restaurant, RestaurantStatus

User = get_user_model()


def create_user(username, role, password="StrongPass123!"):
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
        role=role,
    )


def auth_header(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def create_approved_restaurant(owner, name="Mama's Kitchen"):
    return Restaurant.objects.create(
        owner=owner,
        name=name,
        address="12 Allen Avenue",
        city="Lagos",
        phone_number="08000000000",
        status=RestaurantStatus.APPROVED,
    )


def create_food_item(restaurant, name="Jollof Rice", price="2500.00"):
    category = Category.objects.create(name=f"Category for {name}")
    return FoodItem.objects.create(
        restaurant=restaurant,
        category=category,
        name=name,
        price=price,
        is_available=True,
    )


class BaseAPITestCase(APITestCase):
    """Base class providing a ready-made customer, owner, admin, and rider."""

    def setUp(self):
        self.customer = create_user("customer1", "customer")
        self.owner = create_user("owner1", "restaurant_owner")
        self.admin = create_user("admin1", "admin")
        self.rider = create_user("rider1", "delivery_rider")

        self.restaurant = create_approved_restaurant(self.owner)
        self.food_item = create_food_item(self.restaurant)

    def auth_as(self, user):
        self.client.credentials(**auth_header(user))
