
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


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

    caption = models.CharField(max_length=500, blank=True)

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


class Comment(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vibespace_comments"
    )

    vibe = models.ForeignKey(
        Vibe,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="comments"
    )

    moment = models.ForeignKey(
        Moment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="comments"
    )

    text = models.TextField(max_length=1000)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(vibe__isnull=False, moment__isnull=True)
                    | Q(vibe__isnull=True, moment__isnull=False)
                ),
                name="comment_exactly_one_content"
            ),
        ]
        indexes = [
            models.Index(fields=["vibe", "created_at"]),
            models.Index(fields=["moment", "created_at"]),
        ]

    def __str__(self):
        return f"Comment by {self.author.username}"


class Revibe(models.Model):
    class RevibeType(models.TextChoices):
        DIRECT = "direct", "Direct Revibe"
        QUOTE = "quote", "Quote Revibe"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vibespace_revibes"
    )

    vibe = models.ForeignKey(
        Vibe,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="revibes"
    )

    moment = models.ForeignKey(
        Moment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="revibes"
    )

    revibe_type = models.CharField(
        max_length=10,
        choices=RevibeType.choices,
        default=RevibeType.DIRECT
    )

    quote_text = models.TextField(
        max_length=1000,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(vibe__isnull=False, moment__isnull=True)
                    | Q(vibe__isnull=True, moment__isnull=False)
                ),
                name="revibe_exactly_one_content"
            ),
            models.UniqueConstraint(
                fields=["author", "vibe"],
                condition=Q(vibe__isnull=False),
                name="unique_user_vibe_revibe"
            ),
            models.UniqueConstraint(
                fields=["author", "moment"],
                condition=Q(moment__isnull=False),
                name="unique_user_moment_revibe"
            ),
            models.CheckConstraint(
                condition=(
                    Q(revibe_type="direct", quote_text="")
                    | Q(revibe_type="quote") & ~Q(quote_text="")
                ),
                name="revibe_type_quote_text_consistency"
            ),
        ]
        indexes = [
            models.Index(fields=["vibe", "-created_at"]),
            models.Index(fields=["moment", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.author.username} revibed content"


class SavedContent(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_vibespace_content"
    )

    vibe = models.ForeignKey(
        Vibe,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="saved_by"
    )

    moment = models.ForeignKey(
        Moment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="saved_by"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(vibe__isnull=False, moment__isnull=True)
                    | Q(vibe__isnull=True, moment__isnull=False)
                ),
                name="saved_exactly_one_content"
            ),
            models.UniqueConstraint(
                fields=["user", "vibe"],
                condition=Q(vibe__isnull=False),
                name="unique_user_saved_vibe"
            ),
            models.UniqueConstraint(
                fields=["user", "moment"],
                condition=Q(moment__isnull=False),
                name="unique_user_saved_moment"
            ),
        ]

    def __str__(self):
        return f"Saved content by {self.user.username}"


class Like(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vibespace_likes",
    )

    vibe = models.ForeignKey(
        Vibe,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="likes",
    )

    moment = models.ForeignKey(
        Moment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="likes",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(vibe__isnull=False, moment__isnull=True)
                    | Q(vibe__isnull=True, moment__isnull=False)
                ),
                name="like_exactly_one_content",
            ),
            models.UniqueConstraint(
                fields=["user", "vibe"],
                condition=Q(vibe__isnull=False),
                name="unique_user_vibe_like",
            ),
            models.UniqueConstraint(
                fields=["user", "moment"],
                condition=Q(moment__isnull=False),
                name="unique_user_moment_like",
            ),
        ]
        indexes = [
            models.Index(fields=["vibe", "created_at"]),
            models.Index(fields=["moment", "created_at"]),
        ]

    def __str__(self):
        return f"Like by {self.user.username}"
