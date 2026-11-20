
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework.exceptions import ValidationError, PermissionDenied

from hubs.models import Hub, HubApplication, HubMembership


@transaction.atomic
def submit_application(applicant, data):
    """Create a pending HubApplication for the applicant.

    Prevents multiple pending applications for the same applicant and
    requested slug combination.
    """

    requested_slug = data.get("requested_slug", "").strip()

    if not requested_slug:
        raise ValidationError({
            "requested_slug": "A requested slug is required."
        })

    requested_name = data.get("requested_name", "").strip()
    if not requested_name:
        raise ValidationError({"requested_name": "A Hub name is required."})

    if Hub.objects.filter(slug=requested_slug).exists():
        raise ValidationError({
            "requested_slug": "A Hub already uses this slug."
        })

    if HubApplication.objects.filter(
        requested_slug=requested_slug,
        status=HubApplication.Status.PENDING,
    ).exists():
        raise ValidationError(
            "A pending Hub application already uses this slug."
        )

    existing_pending = HubApplication.objects.filter(
        applicant=applicant,
        requested_slug=requested_slug,
        status=HubApplication.Status.PENDING,
    ).exists()

    if existing_pending:
        raise ValidationError(
            "You already have a pending application for this organisation."
        )

    if HubApplication.objects.filter(
        applicant=applicant,
        requested_slug=requested_slug,
        status=HubApplication.Status.APPROVED,
    ).exists():
        raise ValidationError(
            "This application has already been approved."
        )

    try:
        application = HubApplication.objects.create(
            applicant=applicant,
            requested_name=requested_name,
            requested_slug=requested_slug,
            hub_type=data.get("hub_type"),
            organisation_description=data.get(
                "organisation_description", ""
            ).strip(),
            college_or_parent_organisation=data.get(
                "college_or_parent_organisation", ""
            ).strip(),
            city=data.get("city", "").strip(),
            website=data.get("website", "").strip(),
            contact_email=data.get("contact_email", "").strip(),
            status=HubApplication.Status.PENDING,
        )
    except IntegrityError as exc:
        raise ValidationError(
            "You already have a pending application for this organisation."
        ) from exc

    return application


def _require_staff(reviewer):
    if reviewer is None or not reviewer.is_staff:
        raise PermissionDenied(
            "Only authorised BYB staff can review hub applications."
        )


def _require_not_applicant(reviewer, applicant):
    if reviewer is not None and reviewer.pk == applicant.pk:
        raise PermissionDenied(
            "You cannot review your own hub application."
        )


@transaction.atomic
def approve_application(application, reviewer, review_notes=""):
    """Approve a pending application and create the Hub atomically."""

    _require_staff(reviewer)
    _require_not_applicant(reviewer, application.applicant)

    application = (
        HubApplication.objects
        .select_for_update()
        .filter(pk=application.pk)
        .first()
    )

    if not application:
        raise ValidationError("Hub application not found.")

    if application.status != HubApplication.Status.PENDING:
        raise ValidationError(
            "Only pending applications can be approved."
        )

    # Prevent duplicate Hub creation: an approved application must not
    # already have produced a Hub for this applicant/slug.
    existing_hub = Hub.objects.filter(
        created_by=application.applicant,
        slug=application.requested_slug,
    ).first()

    if existing_hub:
        application.status = HubApplication.Status.APPROVED
        application.reviewer = reviewer
        application.review_notes = review_notes.strip()
        application.reviewed_at = timezone.now()
        application.save(
            update_fields=[
                "status",
                "reviewer",
                "review_notes",
                "reviewed_at",
                "updated_at",
            ]
        )
        return {
            "application": application,
            "hub": existing_hub,
            "created": False,
        }

    hub = Hub.objects.create(
        name=application.requested_name,
        slug=application.requested_slug,
        hub_type=application.hub_type,
        short_description=application.organisation_description,
        description=application.organisation_description,
        website=application.website,
        contact_email=application.contact_email,
        city=application.city,
        college_or_parent_organisation=(
            application.college_or_parent_organisation
        ),
        created_by=application.applicant,
        owner=application.applicant,
        is_verified=False,
        is_active=True,
    )

    HubMembership.objects.create(
        hub=hub,
        user=application.applicant,
        role=HubMembership.Role.OWNER,
        status=HubMembership.Status.APPROVED,
        joined_at=timezone.now(),
    )

    application.status = HubApplication.Status.APPROVED
    application.reviewer = reviewer
    application.review_notes = review_notes.strip()
    application.reviewed_at = timezone.now()
    application.save(
        update_fields=[
            "status",
            "reviewer",
            "review_notes",
            "reviewed_at",
            "updated_at",
        ]
    )

    return {
        "application": application,
        "hub": hub,
        "created": True,
    }


@transaction.atomic
def reject_application(application, reviewer, review_notes=""):
    """Reject a pending application without creating a Hub or membership."""

    _require_staff(reviewer)
    _require_not_applicant(reviewer, application.applicant)

    if not review_notes or not review_notes.strip():
        raise ValidationError({
            "review_notes": "A reason is required when rejecting an application."
        })

    application = (
        HubApplication.objects
        .select_for_update()
        .filter(pk=application.pk)
        .first()
    )

    if not application:
        raise ValidationError("Hub application not found.")

    if application.status != HubApplication.Status.PENDING:
        raise ValidationError(
            "Only pending applications can be rejected."
        )

    application.status = HubApplication.Status.REJECTED
    application.reviewer = reviewer
    application.review_notes = review_notes.strip()
    application.reviewed_at = timezone.now()
    application.save(
        update_fields=[
            "status",
            "reviewer",
            "review_notes",
            "reviewed_at",
            "updated_at",
        ]
    )

    return {
        "application": application,
        "hub": None,
        "created": False,
    }
