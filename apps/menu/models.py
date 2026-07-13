"""
Menu models — spec sections 4.3 Menu Categories and 4.4 Food Menu Management.

FoodItem fields match the spec's table exactly:
    name (String), description (Text), price (Decimal), category (FK),
    restaurant (FK), is_available (Boolean), preparation_time (Integer),
    image (File), rating (Float)
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.restaurants.models import Restaurant


class Category(models.Model):
    """E.g. Fast Food, African Dishes, Drinks, Desserts, Snacks, Vegan Meals."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class FoodItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="food_items")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="food_items")

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)]
    )
    image = models.ImageField(upload_to="food_images/", blank=True, null=True)

    is_available = models.BooleanField(default=True)
    preparation_time = models.PositiveIntegerField(help_text="Estimated prep time in minutes", default=15)

    rating = models.FloatField(default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.restaurant.name}"

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def can_be_published(self):
        """Validation rule: only approved restaurants can publish food items."""
        return self.restaurant.is_approved
