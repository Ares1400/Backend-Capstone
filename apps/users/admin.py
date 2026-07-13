from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "is_active", "is_email_verified", "created_at")
    list_filter = ("role", "is_active", "is_email_verified")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role & Profile", {"fields": ("role", "phone_number", "profile_photo", "is_email_verified")}),
    )


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "is_used", "created_at")
    list_filter = ("is_used",)
