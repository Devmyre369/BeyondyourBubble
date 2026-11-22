
from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import PermissionDenied, ValidationError

from events.models import Event, EventRegistration
from events.permissions import (
    can_manage_hub_event,
    can_submit_hub_event,
)
from hubs.models import Hub, HubMembership
from accounts.models import Notification
from accounts.services.notification_service import (
    create_notification,
    notify_hub_managers,
    notify_staff,
)


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
        create_notification(
            actor=user,
            recipient_id=event.created_by_id,
            event=event,
            hub=event.organising_hub,
            verb=Notification.Verb.EVENT_UPDATED,
        )

    return event


@transaction.atomic
def cancel_event(*, event_id, user, reason):
    """
    Cancel an event before its scheduled start.

    Only the actual Hub Owner can cancel an event.

    The event record and all associated content are preserved.
    Eligible Hub managers, the original submitter, registered
    participants, and Vibe/Moment authors receive notifications.
    Each recipient receives at most one notification.
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

    # Only the actual Hub Owner can cancel an event.
    if (
        not user
        or not user.is_authenticated
        or event.organising_hub.owner_id != user.pk
    ):
        raise PermissionDenied(
            "Only the owner of this Hub can cancel its events."
        )

    # Validate cancellation reason.
    reason = (reason or "").strip()

    if not reason:
        raise ValidationError({
            "reason": "A cancellation reason is required."
        })

    if len(reason) > 1000:
        raise ValidationError({
            "reason": "The cancellation reason cannot exceed 1000 characters."
        })

    # Prevent repeated cancellation and cancellation of completed events.
    if event.status == Event.Status.CANCELLED:
        raise ValidationError({
            "status": "This event has already been cancelled."
        })

    if event.status == Event.Status.COMPLETED:
        raise ValidationError({
            "status": "Completed events cannot be cancelled."
        })

    # Require a scheduled start time.
    if not event.starts_at:
        raise ValidationError({
            "starts_at": "The event must have a scheduled start time."
        })

    # Cancellation is allowed only before the event starts.
    now = timezone.now()

    if event.starts_at <= now:
        raise ValidationError({
            "status": "An event cannot be cancelled after it has started."
        })

    # Preserve the event and all associated records.
    event.status = Event.Status.CANCELLED
    event.cancellation_reason = reason
    event.cancelled_at = now
    event.cancelled_by = user

    event.save(
        update_fields=[
            "status",
            "cancellation_reason",
            "cancelled_at",
            "cancelled_by",
            "updated_at",
        ]
    )

    # Collect all eligible recipients in one set.
    recipient_ids = set()

    # Include approved Hub owners, administrators and editors.
    manager_ids = event.organising_hub.memberships.filter(
        status=HubMembership.Status.APPROVED,
        role__in=[
            HubMembership.Role.OWNER,
            HubMembership.Role.ADMIN,
            HubMembership.Role.EDITOR,
        ],
    ).values_list(
        "user_id",
        flat=True,
    )

    recipient_ids.update(manager_ids)

    # Include the actual Hub Owner.
    recipient_ids.add(event.organising_hub.owner_id)

    # Include the original event submitter.
    recipient_ids.add(event.created_by_id)

    # Include users with active event registrations.
    registered_user_ids = EventRegistration.objects.filter(
        event=event,
        status=EventRegistration.Status.REGISTERED,
    ).values_list(
        "user_id",
        flat=True,
    )

    recipient_ids.update(registered_user_ids)

    # Include authors of event-related Vibes.
    vibe_author_ids = event.vibes.values_list(
        "author_id",
        flat=True,
    )

    recipient_ids.update(vibe_author_ids)

    # Include authors of event-related Moments.
    moment_author_ids = event.moments.values_list(
        "author_id",
        flat=True,
    )

    recipient_ids.update(moment_author_ids)

    # Never notify the cancelling Hub Owner.
    recipient_ids.discard(user.pk)

    # Create one cancellation notification per eligible recipient.
    # create_notification() applies the recipient's notification settings.
    notifications_created = 0

    for recipient_id in recipient_ids:
        notification = create_notification(
            actor=user,
            recipient_id=recipient_id,
            event=event,
            hub=event.organising_hub,
            verb=Notification.Verb.EVENT_CANCELLED,
        )

        if notification is not None:
            notifications_created += 1

    return event, notifications_created
