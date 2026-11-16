
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Hub(models.Model):

    class HubType(models.TextChoices):
        COLLEGE = "college", "College"
        COLLEGE_CLUB = "college_club", "College club"
        COLLEGE_DEPARTMENT = "college_department", "College department"
        ORGANISATION = "organisation", "Organisation"
        COMPANY = "company", "Company"
        COMMUNITY = "community", "Community"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    class MembershipPolicy(models.TextChoices):
        OPEN = "open", "Open"
        APPROVAL_REQUIRED = "approval_required", "Approval required"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(max_length=200)

    slug = models.SlugField(
        max_length=200,
        unique=True,
    )

    hub_type = models.CharField(
        max_length=30,
        choices=HubType.choices,
    )

    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )

    membership_policy = models.CharField(
        max_length=20,
        choices=MembershipPolicy.choices,
        default=MembershipPolicy.APPROVAL_REQUIRED,
    )

    short_description = models.CharField(
        max_length=300,
        blank=True,
    )

    description = models.TextField(blank=True)

    logo = models.URLField(
        max_length=500,
        blank=True,
    )

    cover_image = models.URLField(
        max_length=500,
        blank=True,
    )

    website = models.URLField(
        max_length=500,
        blank=True,
    )

    contact_email = models.EmailField(blank=True)

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    college_or_parent_organisation = models.CharField(
        max_length=200,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_hubs",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_hubs",
    )

    is_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hub_type"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["owner"]),
            models.Index(fields=["is_verified"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.name


class HubMembership(models.Model):

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        EDITOR = "editor", "Editor"
        MEMBER = "member", "Member"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    hub = models.ForeignKey(
        Hub,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hub_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    joined_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["hub", "user"],
                name="unique_hub_membership",
            ),
        ]
        indexes = [
            models.Index(fields=["hub"]),
            models.Index(fields=["user"]),
            models.Index(fields=["role"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.hub.name} ({self.role})"


class HubApplication(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hub_applications",
    )

    requested_name = models.CharField(max_length=200)

    requested_slug = models.SlugField(max_length=200)

    hub_type = models.CharField(
        max_length=30,
        choices=Hub.HubType.choices,
    )

    organisation_description = models.TextField(blank=True)

    college_or_parent_organisation = models.CharField(
        max_length=200,
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    website = models.URLField(
        max_length=500,
        blank=True,
    )

    contact_email = models.EmailField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_hub_applications",
    )

    review_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["applicant", "requested_slug"],
                condition=Q(status="pending"),
                name="unique_pending_hub_application_per_applicant_slug",
            ),
        ]
        indexes = [
            models.Index(fields=["applicant"]),
            models.Index(fields=["status"]),
            models.Index(fields=["hub_type"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.applicant.username} - {self.requested_name} ({self.status})"

