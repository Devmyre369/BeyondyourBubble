
from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from events.models import Event


@transaction.atomic
def review_event(*, event_id, reviewer, decision, review_notes=""):
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

    event.reviewed_by = reviewer
    event.reviewed_at = timezone.now()
    event.review_notes = review_notes.strip()

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
        "updated_at",
    ])

    return event
