"""
Authentication & profile views.

Email verification is fully automatic on registration.
The verify-email endpoint has been removed since it is no longer needed.
"""

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.responses import success_response
from .models import PasswordResetToken
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — create a new account (auto-verified immediately)."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return success_response(
            message="Registration successful. You can now log in.",
            data=UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — obtain JWT access + refresh tokens."""

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class RefreshView(TokenRefreshView):
    """POST /api/auth/refresh/ — exchange a refresh token for a new access token."""

    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist the provided refresh token."""

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logs the user out by blacklisting their refresh token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The refresh token to blacklist"
                ),
            }
        ),
        responses={200: "Logged out successfully"}
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"success": False, "message": "'refresh' token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"success": False, "message": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response(message="Logged out successfully.")


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/profile/ — view or update the authenticated user's profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/ — change password while logged in."""

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Change the authenticated user's password.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["old_password", "new_password"],
            properties={
                "old_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Current password"
                ),
                "new_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="New password (min 8 characters)"
                ),
            }
        ),
        responses={200: "Password changed successfully"}
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"success": False, "message": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return success_response(message="Password changed successfully.")


class PasswordResetRequestView(APIView):
    """POST /api/auth/reset-password/ — request a password reset email."""

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description=(
            "Request a password reset link. Always returns success "
            "regardless of whether the email exists — this prevents "
            "attackers from probing which emails are registered."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="email",
                    description="The registered email address"
                ),
            }
        ),
        responses={200: "Reset link sent if email exists"}
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()
        if user:
            reset_token = PasswordResetToken.objects.create(user=user)
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{reset_token.token}/"
            send_mail(
                subject="Reset your password",
                message=f"Use this link to reset your password: {reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

        return success_response(
            message="If an account with that email exists, a reset link has been sent."
        )


class PasswordResetConfirmView(APIView):
    """POST /api/auth/reset-password/confirm/ — set a new password using a reset token."""

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Confirm a password reset using the token from the reset email.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["token", "new_password"],
            properties={
                "token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="uuid",
                    description="Reset token received via email"
                ),
                "new_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The new password"
                ),
            }
        ),
        responses={200: "Password reset successful"}
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reset_token = get_object_or_404(
            PasswordResetToken, token=serializer.validated_data["token"], is_used=False
        )
        user = reset_token.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        reset_token.is_used = True
        reset_token.save()

        return success_response(message="Password reset successful. You can now log in.")
