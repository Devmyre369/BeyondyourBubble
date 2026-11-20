from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework.exceptions import PermissionDenied, ValidationError

from hubs.models import Hub, HubMembership, HubVerificationRequest
from accounts.models import Notification
from accounts.services.notification_service import create_notification, notify_staff


def _require_staff(reviewer):
    if reviewer is None or not reviewer.is_authenticated or not reviewer.is_staff:
        raise PermissionDenied("Only authorised BYB staff can review verification requests.")


def _reviewer_manages_hub(reviewer, hub):
    if hub.owner_id == reviewer.pk:
        return True
    return HubMembership.objects.filter(
        hub=hub,
        user=reviewer,
        role__in=[HubMembership.Role.OWNER, HubMembership.Role.ADMIN],
        status=HubMembership.Status.APPROVED,
    ).exists()


@transaction.atomic
def request_hub_verification(*, hub_id, requester, request_notes=""):
    hub = Hub.objects.select_for_update().filter(pk=hub_id, is_active=True).first()
    if hub is None:
        raise ValidationError("The requested Hub does not exist or is inactive.")
    if hub.owner_id != requester.pk:
        raise PermissionDenied("Only the Hub owner can request verification.")
    if hub.is_verified:
        raise ValidationError("This Hub is already verified.")
    if HubVerificationRequest.objects.filter(
        hub=hub,
        status=HubVerificationRequest.Status.PENDING,
    ).exists():
        raise ValidationError("A verification request is already pending.")

    try:
        verification_request = HubVerificationRequest.objects.create(
            hub=hub,
            requested_by=requester,
            request_notes=request_notes.strip(),
        )
        notify_staff(
            actor=requester,
            hub=hub,
            verb=Notification.Verb.HUB_VERIFICATION_REQUESTED,
        )
        return verification_request
    except IntegrityError as exc:
        raise ValidationError("A verification request is already pending.") from exc


@transaction.atomic
def review_hub_verification_request(*, request_id, reviewer, decision, review_notes=""):
    _require_staff(reviewer)
    if decision not in ("approve", "reject"):
        raise ValidationError({"decision": "Decision must be approve or reject."})
    if decision == "reject" and not review_notes.strip():
        raise ValidationError({
            "review_notes": "A reason is required when rejecting verification."
        })

    verification_request = (
        HubVerificationRequest.objects.select_for_update()
        .select_related("hub")
        .filter(pk=request_id)
        .first()
    )
    if verification_request is None:
        raise ValidationError("Verification request not found.")
    if verification_request.status != HubVerificationRequest.Status.PENDING:
        raise ValidationError("Only pending verification requests can be reviewed.")

    hub = Hub.objects.select_for_update().get(pk=verification_request.hub_id)
    if _reviewer_manages_hub(reviewer, hub):
        raise PermissionDenied("Hub owners and administrators cannot review their own Hub verification.")

    verification_request.status = (
        HubVerificationRequest.Status.APPROVED
        if decision == "approve"
        else HubVerificationRequest.Status.REJECTED
    )
    verification_request.reviewer = reviewer
    verification_request.review_notes = review_notes.strip()
    verification_request.reviewed_at = timezone.now()
    verification_request.save(update_fields=[
        "status", "reviewer", "review_notes", "reviewed_at",
    ])

    if decision == "approve":
        hub.is_verified = True
        hub.save(update_fields=["is_verified", "updated_at"])

    create_notification(
        actor=reviewer,
        recipient_id=hub.owner_id,
        hub=hub,
        verb=(
            Notification.Verb.HUB_VERIFICATION_APPROVED
            if decision == "approve"
            else Notification.Verb.HUB_VERIFICATION_REJECTED
        ),
    )

    return verification_request
