from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from hubs.models import Hub, HubMembership
from hubs.permissions import can_edit_hub


User = get_user_model()


def get_active_hub(hub_id, *, lock=False):
    queryset = Hub.objects.filter(is_active=True)
    if lock:
        queryset = queryset.select_for_update()

    hub = queryset.filter(pk=hub_id).first()
    if hub is None:
        raise NotFound("Hub not found.")
    return hub


def can_manage_hub_members(user, hub):
    return can_edit_hub(user, hub)


def require_hub_manager(user, hub):
    if not can_manage_hub_members(user, hub):
        raise PermissionDenied(
            "Only the Hub owner or an approved administrator can manage members."
        )


@transaction.atomic
def join_hub(hub_id, user):
    hub = get_active_hub(hub_id, lock=True)
    membership = (
        HubMembership.objects.select_for_update()
        .filter(hub=hub, user=user)
        .first()
    )

    if membership and membership.status == HubMembership.Status.APPROVED:
        raise ValidationError("You are already an approved Hub member.")
    if membership and membership.status == HubMembership.Status.PENDING:
        raise ValidationError("Your membership request is already pending.")

    now = timezone.now()
    status = (
        HubMembership.Status.APPROVED
        if hub.membership_policy == Hub.MembershipPolicy.OPEN
        else HubMembership.Status.PENDING
    )
    joined_at = now if status == HubMembership.Status.APPROVED else None

    if membership:
        membership.role = HubMembership.Role.MEMBER
        membership.status = status
        membership.joined_at = joined_at
        membership.created_at = now
        membership.save(
            update_fields=["role", "status", "joined_at", "created_at"]
        )
    else:
        membership = HubMembership.objects.create(
            hub=hub,
            user=user,
            role=HubMembership.Role.MEMBER,
            status=status,
            joined_at=joined_at,
        )

    return hub, membership


@transaction.atomic
def leave_hub(hub_id, user):
    hub = get_active_hub(hub_id, lock=True)
    membership = (
        HubMembership.objects.select_for_update()
        .filter(hub=hub, user=user)
        .first()
    )

    if membership is None or membership.status != HubMembership.Status.APPROVED:
        raise ValidationError("You do not have an approved membership to leave.")
    if (
        membership.user_id == hub.owner_id
        or membership.role == HubMembership.Role.OWNER
    ):
        raise PermissionDenied(
            "The Hub owner cannot leave while they remain the owner."
        )

    membership.delete()
    return hub


@transaction.atomic
def review_membership_request(hub_id, membership_id, actor, decision):
    hub = get_active_hub(hub_id, lock=True)
    require_hub_manager(actor, hub)

    membership = (
        HubMembership.objects.select_for_update()
        .filter(hub=hub, pk=membership_id)
        .first()
    )
    if membership is None:
        raise NotFound("Membership request not found.")
    if membership.user_id == actor.pk:
        raise PermissionDenied("You cannot review your own membership request.")
    if membership.status != HubMembership.Status.PENDING:
        raise ValidationError("Only pending requests can be reviewed.")
    if decision not in ("approve", "reject"):
        raise ValidationError({"decision": "Choose approve or reject."})

    if decision == "approve":
        membership.status = HubMembership.Status.APPROVED
        membership.role = HubMembership.Role.MEMBER
        membership.joined_at = timezone.now()
    else:
        membership.status = HubMembership.Status.REJECTED
        membership.joined_at = None

    membership.save(update_fields=["status", "role", "joined_at"])
    return membership


@transaction.atomic
def invite_member(hub_id, actor, username):
    hub = get_active_hub(hub_id, lock=True)
    require_hub_manager(actor, hub)

    invited_user = (
        User.objects.select_for_update()
        .filter(
            username__iexact=username,
            is_active=True,
            email_verified=True,
        )
        .first()
    )
    if invited_user is None:
        raise ValidationError({
            "username": "No eligible active, verified user has this username."
        })
    if invited_user.pk == hub.owner_id:
        raise ValidationError({"username": "The Hub owner is already a member."})

    membership = (
        HubMembership.objects.select_for_update()
        .filter(hub=hub, user=invited_user)
        .first()
    )
    if membership and membership.status == HubMembership.Status.APPROVED:
        raise ValidationError({"username": "This user is already a Hub member."})
    if membership and membership.status == HubMembership.Status.PENDING:
        raise ValidationError({
            "username": "This user already has a pending membership request."
        })

    created = membership is None
    now = timezone.now()
    if membership:
        membership.role = HubMembership.Role.MEMBER
        membership.status = HubMembership.Status.APPROVED
        membership.joined_at = now
        membership.created_at = now
        membership.save(
            update_fields=["role", "status", "joined_at", "created_at"]
        )
    else:
        membership = HubMembership.objects.create(
            hub=hub,
            user=invited_user,
            role=HubMembership.Role.MEMBER,
            status=HubMembership.Status.APPROVED,
            joined_at=now,
        )

    return membership, created


@transaction.atomic
def remove_member(hub_id, membership_id, actor):
    hub = get_active_hub(hub_id, lock=True)
    require_hub_manager(actor, hub)

    membership = (
        HubMembership.objects.select_for_update()
        .filter(hub=hub, pk=membership_id)
        .first()
    )
    if membership is None:
        raise NotFound("Hub membership not found.")
    if membership.user_id == actor.pk:
        raise ValidationError("Use the leave Hub action to remove yourself.")
    if (
        membership.user_id == hub.owner_id
        or membership.role == HubMembership.Role.OWNER
    ):
        raise PermissionDenied("The Hub owner cannot be removed.")
    if membership.status != HubMembership.Status.APPROVED:
        raise ValidationError("Only approved members can be removed.")
    if (
        actor.pk != hub.owner_id
        and membership.role
        not in (HubMembership.Role.MEMBER, HubMembership.Role.EDITOR)
    ):
        raise PermissionDenied(
            "Administrators can only remove members and editors."
        )

    membership.delete()
    return hub


@transaction.atomic
def change_member_role(hub_id, membership_id, actor, new_role):
    hub = get_active_hub(hub_id, lock=True)
    require_hub_manager(actor, hub)

    if new_role not in (
        HubMembership.Role.ADMIN,
        HubMembership.Role.EDITOR,
        HubMembership.Role.MEMBER,
    ):
        raise ValidationError({"role": "This role cannot be assigned."})

    membership = (
        HubMembership.objects.select_for_update()
        .filter(hub=hub, pk=membership_id)
        .first()
    )
    if membership is None:
        raise NotFound("Hub membership not found.")
    if membership.user_id == actor.pk:
        raise PermissionDenied("You cannot change your own Hub role.")
    if (
        membership.user_id == hub.owner_id
        or membership.role == HubMembership.Role.OWNER
    ):
        raise PermissionDenied("The Hub owner role cannot be changed.")
    if membership.status != HubMembership.Status.APPROVED:
        raise ValidationError("Only approved members can have their role changed.")
    if actor.pk != hub.owner_id and (
        membership.role == HubMembership.Role.ADMIN
        or new_role == HubMembership.Role.ADMIN
    ):
        raise PermissionDenied(
            "Only the Hub owner can promote or manage administrators."
        )

    membership.role = new_role
    membership.save(update_fields=["role"])
    return membership
