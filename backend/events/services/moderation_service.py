
from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from events.models import Event, EventModerationReview
from accounts.models import Notification
from accounts.services.notification_service import (
    create_notification,
    notify_hub_managers,
)


@transaction.atomic
def review_event(*, event_id, reviewer, decision, review_notes="", review_category=""):
    """
    Approve or reject an event submitted for BYB moderation.

    Only pending events can be reviewed.

    Approval:
    - Sets moderation status to APPROVED.
    - Publishes the event.

    Rejection:
    - Sets moderation status to REJECTED.
    - Keeps the event unpublished.

    Both decisions record the reviewer and review timestamp.
    """

    event = (
        Event.objects
        .select_for_update()
        .filter(id=event_id)
        .first()
    )

    if event is None:
        raise ValidationError({
            "event": "The requested event does not exist."
        })

    if event.moderation_status != Event.ModerationStatus.PENDING:
        raise ValidationError({
            "moderation_status": (
                "This event has already been reviewed "
                "or is not awaiting moderation."
            )
        })

    if decision not in ("approve", "reject"):
        raise ValidationError({
            "decision": "Decision must be approve or reject."
        })

    if decision == "approve" and event.starts_at and event.starts_at <= timezone.now():
        raise ValidationError({
            "starts_at": "An event that has already started cannot be published."
        })

    event.reviewed_by = reviewer
    event.reviewed_at = timezone.now()
    event.review_notes = review_notes.strip()
    event.review_category = review_category if decision == "reject" else ""

    if decision == "approve":
        event.moderation_status = Event.ModerationStatus.APPROVED
        event.status = Event.Status.PUBLISHED
    else:
        event.moderation_status = Event.ModerationStatus.REJECTED
        event.status = Event.Status.DRAFT

    event.save(update_fields=[
        "moderation_status",
        "status",
        "reviewed_by",
        "reviewed_at",
        "review_notes",
        "review_category",
        "updated_at",
    ])

    EventModerationReview.objects.create(
        event=event,
        reviewer=reviewer,
        decision=(
            EventModerationReview.Decision.APPROVED
            if decision == "approve"
            else EventModerationReview.Decision.REJECTED
        ),
        review_notes=event.review_notes,
        review_category=event.review_category,
    )

    approved = decision == "approve"
    verb = (
        Notification.Verb.EVENT_APPROVED
        if approved
        else Notification.Verb.EVENT_REJECTED
    )
    manager_notices = notify_hub_managers(
        actor=reviewer,
        hub=event.organising_hub,
        event=event,
        verb=verb,
    )
    notified_manager_ids = {
        notice.recipient_id
        for notice in manager_notices
        if notice is not None
    }
    if event.created_by_id not in notified_manager_ids:
        create_notification(
            actor=reviewer,
            recipient_id=event.created_by_id,
            verb=verb,
            event=event,
            hub=event.organising_hub,
        )

    return event
