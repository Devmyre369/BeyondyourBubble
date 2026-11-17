
from rest_framework.permissions import BasePermission

from hubs.models import Hub, HubMembership


class CanSubmitHubEvent(BasePermission):
    """
    Only approved owners, administrators, and editors of an active Hub
    can submit events on behalf of that Hub.
    """

    message = (
        "Only approved Hub owners, administrators, and editors "
        "of an active Hub can submit events."
    )

    allowed_roles = (
        HubMembership.Role.OWNER,
        HubMembership.Role.ADMIN,
        HubMembership.Role.EDITOR,
    )

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, hub):
        if not hub.is_active:
            return False

        return HubMembership.objects.filter(
            hub=hub,
            user=request.user,
            status=HubMembership.Status.APPROVED,
            role__in=self.allowed_roles,
        ).exists()
