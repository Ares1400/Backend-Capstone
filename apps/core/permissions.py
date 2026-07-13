"""
Shared, reusable DRF permission classes.

These implement the role-based access control described in the project
spec: Admin, Restaurant Owner, Customer, and (optionally) Delivery Rider.
"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Allows access only to platform admins (staff/superusers or role='admin')."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and (user.is_staff or user.role == "admin")
        )


class IsRestaurantOwner(permissions.BasePermission):
    """Allows access only to users with the restaurant_owner role."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "restaurant_owner")


class IsCustomer(permissions.BasePermission):
    """Allows access only to users with the customer role."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "customer")


class IsDeliveryRider(permissions.BasePermission):
    """Allows access only to users with the delivery_rider role."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "delivery_rider")


class IsOwnerOfRestaurant(permissions.BasePermission):
    """
    Object-level permission: only the restaurant's owner (or an admin) may
    modify the restaurant or its nested resources (menu items, etc).
    Assumes the object either IS a Restaurant or has a `.restaurant` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if user.is_staff or getattr(user, "role", None) == "admin":
            return True

        restaurant = obj if hasattr(obj, "owner") else getattr(obj, "restaurant", None)
        return bool(restaurant and restaurant.owner_id == user.id)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Generic object-level permission: the object's `.user` (or `.customer`)
    must match the requesting user, or the requester is an admin.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff or getattr(user, "role", None) == "admin":
            return True

        owner_field = getattr(obj, "user", None) or getattr(obj, "customer", None)
        return bool(owner_field and owner_field.id == user.id)


class ReadOnlyOrAuthenticated(permissions.BasePermission):
    """Anyone can read (list/retrieve); only authenticated users can write."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)
