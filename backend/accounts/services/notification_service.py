from accounts.models import Notification


def create_notification(
    actor,
    recipient=None,
    verb=None,
    vibe=None,
    moment=None,
    handshake=None,
    event=None,
    hub=None,
    recipient_id=None,
):
    recipient_id = recipient_id or getattr(recipient, "pk", None)
    if actor is None or recipient_id is None or actor.pk == recipient_id:
        return None

    return Notification.objects.create(
        actor=actor,
        recipient_id=recipient_id,
        verb=verb,
        vibe=vibe,
        moment=moment,
        handshake=handshake,
        event=event,
        hub=hub,
    )


def notify_hub_managers(
    *, actor, hub, verb, event=None, roles=None,
):
    """Notify active Hub owners/admins/editors, excluding the acting user."""
    from hubs.models import HubMembership

    if roles is None:
        roles = (
            HubMembership.Role.OWNER,
            HubMembership.Role.ADMIN,
            HubMembership.Role.EDITOR,
        )
    recipients = set(
        hub.memberships.filter(
            status=HubMembership.Status.APPROVED,
            role__in=roles,
        ).values_list("user_id", flat=True)
    )
    recipients.add(hub.owner_id)
    recipients.discard(actor.pk)
    notifications = []
    for recipient_id in recipients:
        notifications.append(create_notification(
            actor=actor,
            recipient_id=recipient_id,
            verb=verb,
            event=event,
            hub=hub,
        ))
    return notifications


def notify_staff(*, actor, verb, event=None, hub=None, exclude_ids=()):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return [
        create_notification(
            actor=actor,
            recipient=recipient,
            verb=verb,
            event=event,
            hub=hub,
        )
        for recipient in User.objects.filter(is_staff=True, is_active=True)
        .exclude(pk__in={actor.pk, *exclude_ids})
    ]
