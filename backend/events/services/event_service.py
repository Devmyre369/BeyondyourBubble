
from django.db import transaction

from rest_framework.exceptions import PermissionDenied

from events.models import Event
from events.permissions import CanSubmitHubEvent
from hubs.models import Hub


@transaction.atomic
def create_event(*, hub, user, validated_data):
    """
    Create an event on behalf of an active Hub.

    Every submitted event starts as a draft awaiting BYB moderation.
    The client cannot override ownership or moderation fields.
    """

    if not isinstance(hub, Hub):
        raise PermissionDenied("A valid organising Hub is required.")

    permission = CanSubmitHubEvent()

    if not permission.has_object_permission(
        request=type(
            "EventSubmissionRequest",
            (),
            {"user": user},
        )(),
        view=None,
        hub=hub,
    ):
        raise PermissionDenied(permission.message)

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
