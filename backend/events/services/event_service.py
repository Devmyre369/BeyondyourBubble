
from django.db import transaction

from rest_framework.exceptions import PermissionDenied

from events.models import Event
from events.permissions import can_submit_hub_event
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

    Ownership and moderation fields are controlled by the backend.
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

    return event
