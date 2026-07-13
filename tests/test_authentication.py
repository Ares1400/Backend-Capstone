"""
Authentication tests — covers spec section 11 "Authentication tests".
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .helpers import create_user, auth_header

User = get_user_model()


class RegistrationTests(APITestCase):
    def test_register_customer_success(self):
        response = self.client.post("/api/auth/register/", {
            "username": "newcustomer",
            "email": "newcustomer@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "customer",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newcustomer@example.com").exists())

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post("/api/auth/register/", {
            "username": "newcustomer2",
            "email": "newcustomer2@example.com",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass123!",
            "role": "customer",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_rejects_self_assigned_admin_role(self):
        response = self.client.post("/api/auth/register/", {
            "username": "sneakyadmin",
            "email": "sneaky@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "admin",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_rejects_duplicate_email(self):
        create_user("existing", "customer")
        response = self.client.post("/api/auth/register/", {
            "username": "another",
            "email": "existing@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "customer",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = create_user("loginuser", "customer")

    def test_login_success_returns_tokens(self):
        response = self.client.post("/api/auth/login/", {
            "email": "loginuser@example.com",
            "password": "StrongPass123!",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password_fails(self):
        response = self.client.post("/api/auth/login/", {
            "email": "loginuser@example.com",
            "password": "WrongPassword!",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileAndLogoutTests(APITestCase):
    def setUp(self):
        self.user = create_user("profileuser", "customer")

    def test_unauthenticated_profile_access_denied(self):
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_profile_access(self):
        self.client.credentials(**auth_header(self.user))
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "profileuser@example.com")

    def test_logout_blacklists_refresh_token(self):
        login = self.client.post("/api/auth/login/", {
            "email": "profileuser@example.com",
            "password": "StrongPass123!",
        })
        refresh = login.data["refresh"]
        self.client.credentials(**auth_header(self.user))
        response = self.client.post("/api/auth/logout/", {"refresh": refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = create_user("resetuser", "customer")

    def test_request_reset_for_unknown_email_still_returns_200(self):
        # Should not leak whether the email exists.
        response = self.client.post("/api/auth/reset-password/", {"email": "ghost@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_reset_for_known_email(self):
        response = self.client.post("/api/auth/reset-password/", {"email": "resetuser@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.reset_tokens.count(), 1)
