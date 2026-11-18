
from django.db import transaction

from rest_framework.exceptions import PermissionDenied, ValidationError

from events.models import Event
from events.permissions import (
    can_manage_hub_event,
    can_submit_hub_event,
)
from hubs.models import Hub


@transaction.atomic
def create_event(*, hub, user, validated_data):
    """
    Create an event on behalf of an active Hub.

    Every newly submitted event:
    - Belongs to an organising Hub.
    - Records the submitting user.
    - Starts as a draft.
    - Requires BYB moderation approval.
    """

    if not isinstance(hub, Hub):
        raise PermissionDenied(
            "A valid organising Hub is required."
        )

    if not can_submit_hub_event(user=user, hub=hub):
        raise PermissionDenied(
            "Only approved Hub owners, administrators, and editors "
            "of an active Hub can submit events."
        )

    return Event.objects.create(
        **validated_data,
        organising_hub=hub,
        created_by=user,
        status=Event.Status.DRAFT,
        moderation_status=Event.ModerationStatus.PENDING,
        reviewed_by=None,
        reviewed_at=None,
        review_notes="",
    )


@transaction.atomic
def update_event(*, event_id, user, validated_data):
    """
    Update an event belonging to a Hub.

    Any approved or rejected event that is edited must go through
    BYB moderation again.

    Pending events remain pending when edited.
    Cancelled and completed events cannot be edited.
    """

    event = (
        Event.objects
        .select_for_update()
        .select_related("organising_hub")
        .filter(id=event_id)
        .first()
    )

    if event is None:
        raise ValidationError({
            "event": "The requested event does not exist."
        })

    if not can_manage_hub_event(user=user, event=event):
        raise PermissionDenied(
            "You do not have permission to manage this Hub event."
        )

    if event.status in [
        Event.Status.CANCELLED,
        Event.Status.COMPLETED,
    ]:
        raise ValidationError({
            "status": "Cancelled or completed events cannot be edited."
        })

    for field, value in validated_data.items():
        setattr(event, field, value)

    if event.moderation_status in [
        Event.ModerationStatus.APPROVED,
        Event.ModerationStatus.REJECTED,
    ]:
        event.status = Event.Status.DRAFT
        event.moderation_status = Event.ModerationStatus.PENDING
        event.reviewed_by = None
        event.reviewed_at = None
        event.review_notes = ""

    event.save()

    return event


@transaction.atomic
def cancel_event(*, event_id, user):
    """
    Cancel a published event belonging to a Hub.

    Only approved Hub owners, administrators, and editors
    can cancel events belonging to their Hub.
    """

    event = (
        Event.objects
        .select_for_update()
        .select_related("organising_hub")
        .filter(id=event_id)
        .first()
    )

    if event is None:
        raise ValidationError({
            "event": "The requested event does not exist."
        })

    if not can_manage_hub_event(user=user, event=event):
        raise PermissionDenied(
            "You do not have permission to manage this Hub event."
        )

    if (
        event.status != Event.Status.PUBLISHED
        or event.moderation_status != Event.ModerationStatus.APPROVED
    ):
        raise ValidationError({
            "status": "Only approved, published events can be cancelled."
        })

    event.status = Event.Status.CANCELLED
    event.save(update_fields=["status", "updated_at"])

    return event
