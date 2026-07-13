"""
Restaurant model — spec section 4.2 Restaurant Management.

Covers: registration, admin approval system, profile management,
location/contact info, opening hours.
"""

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class RestaurantStatus(models.TextChoices):
    PENDING = "pending", "Pending Approval"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    SUSPENDED = "suspended", "Suspended"


class Restaurant(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="restaurants"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="restaurant_logos/", blank=True, null=True)

    # Location & contact
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Nigeria")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    # Opening hours (simple text spec to keep model lean, e.g. "Mon-Sun 08:00-22:00")
    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)
    is_open_now = models.BooleanField(default=True)

    # Approval workflow (spec 4.2 + 3.1 Admin permission "Approve/reject restaurants")
    status = models.CharField(max_length=20, choices=RestaurantStatus.choices, default=RestaurantStatus.PENDING)
    rejection_reason = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)  # used for admin "suspend" action

    average_rating = models.FloatField(default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Restaurant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_approved(self):
        return self.status == RestaurantStatus.APPROVED
