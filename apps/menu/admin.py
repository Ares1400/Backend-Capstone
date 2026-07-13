from django.contrib import admin

from .models import Category, FoodItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "category", "price", "is_available", "rating")
    list_filter = ("is_available", "category", "restaurant")
    search_fields = ("name", "restaurant__name")
