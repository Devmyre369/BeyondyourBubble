
from rest_framework.permissions import BasePermission

from hubs.models import HubMembership


ALLOWED_EVENT_SUBMISSION_ROLES = (
    HubMembership.Role.OWNER,
    HubMembership.Role.ADMIN,
    HubMembership.Role.EDITOR,
)


def can_submit_hub_event(*, user, hub):
    """
    Check whether a user can submit or manage events for a Hub.

    Requirements:
    - User must be authenticated.
    - Hub must be active.
    - Membership must be approved.
    - Role must be OWNER, ADMIN, or EDITOR.
    """

    if not user or not user.is_authenticated:
        return False

    if not hub or not hub.is_active:
        return False

    return HubMembership.objects.filter(
        hub=hub,
        user=user,
        status=HubMembership.Status.APPROVED,
        role__in=ALLOWED_EVENT_SUBMISSION_ROLES,
    ).exists()


def can_manage_hub_event(*, user, event):
    """
    Check whether a user can manage an event belonging to a Hub.

    Event management is Hub-based, not creator-based.
    Eligible managers can manage every event belonging to their Hub.
    """

    if not event:
        return False

    return can_submit_hub_event(
        user=user,
        hub=event.organising_hub,
    )


class CanSubmitHubEvent(BasePermission):
    """
    DRF permission for submitting events through an active Hub.
    """

    message = (
        "Only approved Hub owners, administrators, and editors "
        "of an active Hub can submit events."
    )

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, hub):
        return can_submit_hub_event(
            user=request.user,
            hub=hub,
        )
