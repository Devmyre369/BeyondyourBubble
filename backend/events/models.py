from django.db import models

# Create your models here.

import uuid

from django.conf import settings
from django.db import models


class Event(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    organiser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organised_events"
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    starts_at = models.DateTimeField(
        null=True,
        blank=True
    )

    ends_at = models.DateTimeField(
        null=True,
        blank=True
    )

    venue_name = models.CharField(
        max_length=200,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
