"""
Serializers for registration, profile management, and password reset.

Note: login itself is handled by SimpleJWT's TokenObtainPairView with a
custom serializer (below) so the JWT payload also returns role + user id.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "password", "password_confirm",
            "first_name", "last_name", "phone_number", "role",
        )
        read_only_fields = ("id",)

    def validate_role(self, value):
        # Admin accounts are never created through public self-registration.
        if value == Role.ADMIN:
            raise serializers.ValidationError("You cannot self-register as an admin.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Read/update serializer for the authenticated user's own profile."""

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "last_name",
            "phone_number", "role", "profile_photo", "is_email_verified",
            "created_at",
        )
        read_only_fields = ("id", "email", "role", "is_email_verified", "created_at")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends SimpleJWT's default serializer so the access/refresh token
    response also includes basic user info — saves the frontend an
    extra round trip after login.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
        }
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
