from django.db import models

# Create your models here.

import uuid

from django.conf import settings
from django.db import models


class Vibe(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vibes"
    )

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vibes"
    )

    text = models.TextField(max_length=2000)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["author", "-created_at"]),
            models.Index(fields=["event", "-created_at"]),
        ]

    def __str__(self):
        return f"Vibe by {self.author.username}"


class Moment(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="moments"
    )

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moments"
    )

    image_url = models.URLField(max_length=500)

    cloudinary_public_id = models.CharField(
        max_length=255,
        blank=True
    )

    caption = models.CharField(
        max_length=500,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["author", "-created_at"]),
            models.Index(fields=["event", "-created_at"]),
        ]

    def __str__(self):
        return f"Moment by {self.author.username}"
