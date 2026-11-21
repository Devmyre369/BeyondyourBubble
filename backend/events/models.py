
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

    class RejectionCategory(models.TextChoices):
        INCOMPLETE = "incomplete", "Incomplete information"
        UNVERIFIABLE = "unverifiable", "Invalid or unverifiable details"
        DUPLICATE = "duplicate", "Duplicate event"
        MISLEADING = "misleading", "Misleading information"
        POLICY = "policy_violation", "Policy violation"
        INAPPROPRIATE = "inappropriate", "Inappropriate content"
        OTHER = "other", "Other"

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
    review_category = models.CharField(
        max_length=24,
        choices=RejectionCategory.choices,
        blank=True,
    )

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


class EventModerationReview(models.Model):
    """Immutable audit entry for each BYB moderation decision."""

    class Decision(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class RejectionCategory(models.TextChoices):
        INCOMPLETE = "incomplete", "Incomplete information"
        UNVERIFIABLE = "unverifiable", "Invalid or unverifiable details"
        DUPLICATE = "duplicate", "Duplicate event"
        MISLEADING = "misleading", "Misleading information"
        POLICY = "policy_violation", "Policy violation"
        INAPPROPRIATE = "inappropriate", "Inappropriate content"
        OTHER = "other", "Other"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="moderation_history",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_moderation_reviews",
    )
    decision = models.CharField(max_length=10, choices=Decision.choices)
    review_notes = models.TextField(blank=True)
    review_category = models.CharField(
        max_length=24,
        choices=RejectionCategory.choices,
        blank=True,
    )
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reviewed_at"]

    def __str__(self):
        return f"{self.event.title}: {self.get_decision_display()}"


class EventRegistration(models.Model):
    class Status(models.TextChoices):
        REGISTERED = "registered", "Registered"
        CANCELLED = "cancelled", "Cancelled"

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="registrations",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="event_registrations",
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.REGISTERED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"], name="unique_event_registration",
            ),
        ]
        indexes = [models.Index(fields=["user", "status"], name="evt_reg_user_status_idx")]

