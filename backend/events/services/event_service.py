
from django.db import transaction

from rest_framework.exceptions import PermissionDenied, ValidationError

from events.models import Event
from events.permissions import (
    can_manage_hub_event,
    can_submit_hub_event,
)
from hubs.models import Hub
from accounts.models import Notification
from accounts.services.notification_service import notify_hub_managers, notify_staff


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

    event = Event.objects.create(
        **validated_data,
        organising_hub=hub,
        created_by=user,
        status=Event.Status.DRAFT,
        moderation_status=Event.ModerationStatus.PENDING,
        reviewed_by=None,
        reviewed_at=None,
        review_notes="",
    )
    manager_notices = notify_hub_managers(
        actor=user,
        hub=hub,
        event=event,
        verb=Notification.Verb.EVENT_SUBMITTED,
    )
    notify_staff(
        actor=user,
        event=event,
        hub=hub,
        verb=Notification.Verb.EVENT_SUBMITTED,
        exclude_ids={
            notice.recipient_id
            for notice in manager_notices
            if notice is not None
        },
    )
    return event


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
        # Keep the most recent decision visible while this revision is
        # pending. Each decision also has an immutable history record.

    event.save()

    notified_manager_ids = {
        notice.recipient_id
        for notice in notify_hub_managers(
            actor=user,
            hub=event.organising_hub,
            event=event,
            verb=Notification.Verb.EVENT_UPDATED,
        )
        if notice is not None
    }
    if event.created_by_id not in notified_manager_ids:
        from accounts.services.notification_service import create_notification

        create_notification(
            actor=user,
            recipient_id=event.created_by_id,
            event=event,
            hub=event.organising_hub,
            verb=Notification.Verb.EVENT_UPDATED,
        )

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
    notified_manager_ids = {
        notice.recipient_id
        for notice in notify_hub_managers(
            actor=user,
            hub=event.organising_hub,
            event=event,
            verb=Notification.Verb.EVENT_CANCELLED,
        )
        if notice is not None
    }
    if event.created_by_id not in notified_manager_ids:
        from accounts.services.notification_service import create_notification

        create_notification(
            actor=user,
            recipient_id=event.created_by_id,
            event=event,
            hub=event.organising_hub,
            verb=Notification.Verb.EVENT_CANCELLED,
        )

    return event
