from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import HubMembership


def can_edit_hub(user, hub):
    if not user or not user.is_authenticated:
        return False
    if hub.owner_id == user.pk:
        return True
    return hub.memberships.filter(
        user=user,
        role=HubMembership.Role.ADMIN,
        status=HubMembership.Status.APPROVED,
    ).exists()


class CanEditHub(BasePermission):
    def has_object_permission(self, request, view, hub):
        if request.method in SAFE_METHODS:
            return True
        if not can_edit_hub(request.user, hub):
            return False
        if (
            "membership_policy" in request.data
            and hub.owner_id != request.user.pk
        ):
            return False
        return True
