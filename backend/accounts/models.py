
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


# ==================================================
# USER MODEL
# ==================================================

class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    email = models.EmailField(
        unique=True,
        db_index=True
    )

    email_verified = models.BooleanField(default=False)

    onboarding_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# ==================================================
# INDIVIDUAL USER PROFILE / VIBESPACE
# ==================================================

class Profile(models.Model):

    class ProfileType(models.TextChoices):
        STUDENT = "student", "Student"
        PROFESSIONAL = "professional", "Professional"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # One profile belongs to exactly one user.
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    # Profile identity
    profile_type = models.CharField(
        max_length=20,
        choices=ProfileType.choices
    )

    byb_signature = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )

    bio = models.CharField(
        max_length=500,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    # Profile images
    profile_picture = models.URLField(
        max_length=500,
        blank=True
    )

    cover_image = models.URLField(
        max_length=500,
        blank=True
    )

    # Student information
    institution = models.CharField(
        max_length=200,
        blank=True
    )

    course = models.CharField(
        max_length=150,
        blank=True
    )

    field_of_study = models.CharField(
        max_length=150,
        blank=True
    )

    academic_year = models.CharField(
        max_length=50,
        blank=True
    )

    graduation_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    # Professional information
    current_organization = models.CharField(
        max_length=200,
        blank=True
    )

    job_title = models.CharField(
        max_length=150,
        blank=True
    )

    industry = models.CharField(
        max_length=150,
        blank=True
    )

    experience_years = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    # Shared interests and skills
    interests = models.JSONField(
        default=list,
        blank=True
    )

    skills = models.JSONField(
        default=list,
        blank=True
    )

    # Social links
    linkedin_url = models.URLField(
        max_length=500,
        blank=True
    )

    github_url = models.URLField(
        max_length=500,
        blank=True
    )

    website_url = models.URLField(
        max_length=500,
        blank=True
    )

    # Privacy
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s VibeSpace"


class Follow(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following_relationships",
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower_relationships",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="accounts_unique_follow_pair",
            ),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("following")),
                name="accounts_no_self_follow",
            ),
        ]
        indexes = [
            models.Index(
                fields=["follower", "created_at"],
                name="accounts_follow_out_idx",
            ),
            models.Index(
                fields=["following", "created_at"],
                name="accounts_follow_in_idx",
            ),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Handshake(models.Model):
    """A private, auditable connection request between two BYB users."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="handshake_requests_sent",
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="handshake_requests_received",
    )
    # Canonical participant order gives the database a direction-independent
    # uniqueness key for pending and accepted relationships.
    user_low = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="handshake_pairs_low",
        editable=False,
    )
    user_high = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="handshake_pairs_high",
        editable=False,
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handshake_responses",
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handshake_cancellations",
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(requester=models.F("recipient")),
                name="accounts_handshake_no_self",
            ),
            models.CheckConstraint(
                condition=models.Q(user_low__lt=models.F("user_high")),
                name="accounts_handshake_pair_order",
            ),
            models.UniqueConstraint(
                fields=["user_low", "user_high"],
                condition=models.Q(status__in=["pending", "accepted"]),
                name="accounts_handshake_one_active_pair",
            ),
        ]
        indexes = [
            models.Index(
                fields=["recipient", "status", "created_at"],
                name="accounts_handshake_in_idx",
            ),
            models.Index(
                fields=["requester", "status", "created_at"],
                name="accounts_handshake_out_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.requester_id and self.recipient_id:
            low, high = sorted((self.requester_id, self.recipient_id), key=str)
            self.user_low_id = low
            self.user_high_id = high
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.requester.username} → {self.recipient.username} ({self.status})"


class Notification(models.Model):
    class Verb(models.TextChoices):
        LIKE = "like", "Liked your post"
        COMMENT = "comment", "Commented on your post"
        SAVE = "save", "Saved your post"
        SHARE = "share", "Shared your post"
        FOLLOW = "follow", "Started following you"
        REVIBE = "revibe", "Revibed your post"
        HANDSHAKE_REQUEST = "handshake_request", "Sent you a Handshake request"
        HANDSHAKE_ACCEPTED = "handshake_accepted", "Accepted your Handshake request"
        EVENT_APPROVED = "event_approved", "Approved your event"
        EVENT_REJECTED = "event_rejected", "Needs changes to your event"
        EVENT_SUBMITTED = "event_submitted", "Submitted an event for review"
        EVENT_UPDATED = "event_updated", "Updated a Hub event"
        EVENT_CANCELLED = "event_cancelled", "Cancelled a Hub event"
        HUB_APPLICATION_APPROVED = "hub_application_approved", "Approved your Hub application"
        HUB_APPLICATION_REJECTED = "hub_application_rejected", "Rejected your Hub application"
        HUB_APPLICATION_SUBMITTED = "hub_application_submitted", "Submitted a Hub application"
        HUB_MEMBERSHIP_REQUEST = "hub_membership_request", "Requested to join your Hub"
        HUB_MEMBER_JOINED = "hub_member_joined", "Joined your Hub"
        HUB_MEMBER_LEFT = "hub_member_left", "Left your Hub"
        HUB_MEMBERSHIP_APPROVED = "hub_membership_approved", "Approved your Hub membership"
        HUB_MEMBERSHIP_REJECTED = "hub_membership_rejected", "Rejected your Hub membership"
        HUB_INVITED = "hub_invited", "Added you to a Hub"
        HUB_MEMBER_REMOVED = "hub_member_removed", "Removed you from a Hub"
        HUB_ROLE_CHANGED = "hub_role_changed", "Changed your Hub role"
        HUB_VERIFICATION_APPROVED = "hub_verification_approved", "Verified your Hub"
        HUB_VERIFICATION_REJECTED = "hub_verification_rejected", "Declined your Hub verification request"
        HUB_VERIFICATION_REQUESTED = "hub_verification_requested", "Requested Hub verification"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications_received",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications_sent",
    )
    verb = models.CharField(max_length=32, choices=Verb.choices)
    vibe = models.ForeignKey(
        "vibespace.Vibe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    moment = models.ForeignKey(
        "vibespace.Moment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    handshake = models.ForeignKey(
        "accounts.Handshake",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    hub = models.ForeignKey(
        "hubs.Hub",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "-created_at"],
                name="accounts_notif_recency_idx",
            ),
            models.Index(
                fields=["recipient", "read_at"],
                name="accounts_notif_unread_idx",
            ),
        ]

    def __str__(self):
        return f"{self.actor.username} {self.verb} for {self.recipient.username}"


# ==================================================
# PENDING SIGNUP
# ==================================================

class PendingSignup(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    username = models.CharField(
        max_length=150,
        unique=True
    )

    email = models.EmailField(unique=True)

    password_hash = models.CharField(max_length=128)

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} - {self.email}"


# ==================================================
# EMAIL OTP
# ==================================================

class EmailOTP(models.Model):

    class Purpose(models.TextChoices):
        SIGNUP = "signup", "Signup"
        PASSWORD_RESET = "password_reset", "Password Reset"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    email = models.EmailField(db_index=True)

    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices
    )

    otp_hash = models.CharField(max_length=128)

    attempts = models.PositiveSmallIntegerField(default=0)

    expires_at = models.DateTimeField()

    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.purpose}"


# ==================================================
# USER SETTINGS
# ==================================================

class UserSettings(models.Model):
    """Persisted, per-user application settings."""

    class Theme(models.TextChoices):
        DARK = "dark", "Dark"
        LIGHT = "light", "Light"
        SYSTEM = "system", "System default"

    class ProfileVisibility(models.TextChoices):
        EVERYONE = "everyone", "Everyone"
        REGISTERED = "registered", "Registered BYB users"
        CONNECTIONS = "connections", "Approved connections"

    class HandshakePermission(models.TextChoices):
        EVERYONE = "everyone", "Everyone"
        REGISTERED = "registered", "Registered BYB users"
        CONNECTIONS = "connections", "Approved connections"

    class VibeInteractionPermission(models.TextChoices):
        EVERYONE = "everyone", "Everyone"
        REGISTERED = "registered", "Registered BYB users"
        CONNECTIONS = "connections", "Approved connections"

    class Density(models.TextChoices):
        COMFORTABLE = "comfortable", "Comfortable"
        COMPACT = "compact", "Compact"

    class Language(models.TextChoices):
        EN = "en", "English"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="settings",
    )

    theme = models.CharField(
        max_length=10,
        choices=Theme.choices,
        default=Theme.DARK,
    )

    mute_optional_notifications = models.BooleanField(default=False)
    in_app_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=False)

    event_updates = models.BooleanField(default=True)
    event_registration_updates = models.BooleanField(default=True)
    event_reminders = models.BooleanField(default=True)
    event_cancellations = models.BooleanField(default=True)
    hub_announcements = models.BooleanField(default=True)
    hub_activity = models.BooleanField(default=True)
    handshake_requests = models.BooleanField(default=True)
    vibe_interactions = models.BooleanField(default=True)
    likes_and_comments = models.BooleanField(default=True)
    byb_announcements = models.BooleanField(default=True)

    profile_visibility = models.CharField(
        max_length=20,
        choices=ProfileVisibility.choices,
        default=ProfileVisibility.REGISTERED,
    )
    discoverable = models.BooleanField(default=True)
    handshake_permission = models.CharField(
        max_length=20,
        choices=HandshakePermission.choices,
        default=HandshakePermission.REGISTERED,
    )
    vibe_interaction_permission = models.CharField(
        max_length=20,
        choices=VibeInteractionPermission.choices,
        default=VibeInteractionPermission.REGISTERED,
    )

    preferred_city = models.CharField(max_length=100, blank=True)
    language = models.CharField(
        max_length=10,
        choices=Language.choices,
        default=Language.EN,
    )
    density = models.CharField(
        max_length=20,
        choices=Density.choices,
        default=Density.COMFORTABLE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user.username}"
