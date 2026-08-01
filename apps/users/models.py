"""
Custom User model with role-based access control.

Roles map directly onto the spec's "3. User Roles" section:
    - admin            -> 3.1 Admin
    - restaurant_owner -> 3.2 Restaurant Owner / Admin
    - customer         -> 3.3 Customer (User)
    - delivery_rider   -> 3.4 Delivery Rider

Email verification is automatic on registration — no email link needed.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    RESTAURANT_OWNER = "restaurant_owner", "Restaurant Owner"
    CUSTOMER = "customer", "Customer"
    DELIVERY_RIDER = "delivery_rider", "Delivery Rider"


class User(AbstractUser):
    """
    Extends Django's AbstractUser with role, phone number, profile photo,
    and email-verification fields. Email is unique and used to log in.
    """

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)

    # Auto-verified on registration — no email link needed
    is_email_verified = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == Role.ADMIN or self.is_staff

    @property
    def is_restaurant_owner(self):
        return self.role == Role.RESTAURANT_OWNER

    @property
    def is_customer(self):
        return self.role == Role.CUSTOMER

    @property
    def is_delivery_rider(self):
        return self.role == Role.DELIVERY_RIDER


class PasswordResetToken(models.Model):
    """One-time token issued for the 'forgot password' flow."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset token for {self.user.email}"
