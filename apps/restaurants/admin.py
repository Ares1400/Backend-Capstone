from django.contrib import admin

from .models import Restaurant


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "city", "status", "is_active", "average_rating", "created_at")
    list_filter = ("status", "is_active", "city")
    search_fields = ("name", "owner__username", "city")
    prepopulated_fields = {"slug": ("name",)}
