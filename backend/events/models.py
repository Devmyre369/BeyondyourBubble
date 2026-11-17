
import uuid

from django.conf import settings
from django.db import models


class Event(models.Model):

    class Category(models.TextChoices):
        TECHNICAL = "technical", "Technical"
        CULTURAL = "cultural", "Cultural"
        ACADEMIC = "academic", "Academic"
        SPORTS = "sports", "Sports"
        BUSINESS = "business", "Business & Entrepreneurship"
        ENTERTAINMENT = "entertainment", "Entertainment"
        SOCIAL = "social", "Social & Community"
        POLITICAL = "political", "Political & Public Affairs"
        WORKSHOP = "workshop", "Workshop & Seminar"
        OTHER = "other", "Other"

    class Format(models.TextChoices):
        OFFLINE = "offline", "Offline"
        ONLINE = "online", "Online"
        HYBRID = "hybrid", "Hybrid"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    class ModerationStatus(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Event ownership and submission
    organising_hub = models.ForeignKey(
        "hubs.Hub",
        on_delete=models.PROTECT,
        related_name="events",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_events",
    )

    # Basic event information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
    )

    cover_image_url = models.URLField(
        max_length=500,
        blank=True,
    )

    cover_image_public_id = models.CharField(
        max_length=255,
        blank=True,
    )

    # Event schedule
    starts_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    ends_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Event format
    format = models.CharField(
        max_length=20,
        choices=Format.choices,
        default=Format.OFFLINE,
    )

    # Physical location
    venue_name = models.CharField(
        max_length=200,
        blank=True,
    )

    venue_address = models.TextField(blank=True)

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    # Online participation
    online_join_url = models.URLField(
        max_length=500,
        blank=True,
    )

    online_access_instructions = models.TextField(
        blank=True,
    )

    # Event lifecycle
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # BYB moderation
    moderation_status = models.CharField(
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_events",
    )

    review_notes = models.TextField(blank=True)

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "moderation_status", "starts_at"],
                name="event_discovery_idx",
            ),
            models.Index(
                fields=["city", "category"],
                name="event_city_category_idx",
            ),
        ]

    def __str__(self):
        return self.title
