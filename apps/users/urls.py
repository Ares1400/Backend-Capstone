from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    RefreshView,
    ProfileView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("profile/", ProfileView.as_view(), name="auth-profile"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("reset-password/", PasswordResetRequestView.as_view(), name="auth-reset-password"),
    path("reset-password/confirm/", PasswordResetConfirmView.as_view(), name="auth-reset-password-confirm"),
]
