from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("food_name", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "restaurant", "status", "total", "created_at")
    list_filter = ("status", "restaurant")
    search_fields = ("customer__username", "restaurant__name")
    inlines = [OrderItemInline]
