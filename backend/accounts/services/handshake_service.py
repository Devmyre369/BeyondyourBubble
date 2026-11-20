from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from accounts.models import Handshake, Notification, Profile
from accounts.services.notification_service import create_notification


User = get_user_model()


def _active_public_target(user):
    return (
        user.is_active
        and user.email_verified
        and Profile.objects.filter(
            user=user,
            visibility=Profile.Visibility.PUBLIC,
        ).exists()
    )


def _active_pair(first, second):
    low_id, high_id = sorted((first.pk, second.pk), key=str)
    return Handshake.objects.filter(
        user_low_id=low_id,
        user_high_id=high_id,
        status__in=[Handshake.Status.PENDING, Handshake.Status.ACCEPTED],
    )


def send_handshake_request(requester, recipient):
    if not requester.is_active or not requester.email_verified:
        raise PermissionDenied("A verified active account is required to send Handshake requests.")
    if requester.pk == recipient.pk:
        raise ValidationError({"recipient": "You cannot send a Handshake request to yourself."})
    if not _active_public_target(recipient):
        raise NotFound("This profile is not available for Handshake requests.")

    try:
        with transaction.atomic():
            list(
                User.objects.select_for_update()
                .filter(pk__in=[requester.pk, recipient.pk])
                .order_by("pk")
            )
            existing = _active_pair(requester, recipient).select_for_update().first()
            if existing:
                return existing, False

            handshake = Handshake.objects.create(
                requester=requester,
                recipient=recipient,
                status=Handshake.Status.PENDING,
            )
            create_notification(
                requester,
                recipient,
                Notification.Verb.HANDSHAKE_REQUEST,
                handshake=handshake,
            )
            return handshake, True
    except IntegrityError:
        # The conditional unique constraint is the final guard against two
        # concurrent sends (including a request in the opposite direction).
        existing = _active_pair(requester, recipient).first()
        if existing:
            return existing, False
        raise


def _get_pending_for_update(handshake_id):
    try:
        return Handshake.objects.select_for_update().get(pk=handshake_id)
    except Handshake.DoesNotExist as error:
        raise NotFound("Handshake request not found.") from error


def _mark_request_notifications_read(handshake):
    Notification.objects.filter(
        handshake=handshake,
        verb=Notification.Verb.HANDSHAKE_REQUEST,
        read_at__isnull=True,
    ).update(read_at=timezone.now())


@transaction.atomic
def respond_to_handshake(user, handshake_id, accept):
    handshake = _get_pending_for_update(handshake_id)
    if handshake.recipient_id != user.pk:
        raise PermissionDenied("Only the recipient can respond to this request.")
    if handshake.status != Handshake.Status.PENDING:
        raise ValidationError("This Handshake request is no longer pending.")

    now = timezone.now()
    handshake.status = (
        Handshake.Status.ACCEPTED if accept else Handshake.Status.REJECTED
    )
    handshake.responded_by = user
    handshake.responded_at = now
    handshake.save(update_fields=["status", "responded_by", "responded_at", "updated_at"])
    _mark_request_notifications_read(handshake)

    if accept:
        create_notification(
            user,
            handshake.requester,
            Notification.Verb.HANDSHAKE_ACCEPTED,
            handshake=handshake,
        )
    return handshake


@transaction.atomic
def cancel_handshake(user, handshake_id, remove_accepted=False):
    handshake = _get_pending_for_update(handshake_id)
    if handshake.status == Handshake.Status.PENDING:
        if handshake.requester_id != user.pk:
            raise PermissionDenied("Only the sender can cancel this pending request.")
    elif handshake.status == Handshake.Status.ACCEPTED and remove_accepted:
        if user.pk not in (handshake.requester_id, handshake.recipient_id):
            raise PermissionDenied("Only a connected user can remove this connection.")
    else:
        raise ValidationError("This Handshake cannot be cancelled in its current state.")

    handshake.status = Handshake.Status.CANCELLED
    handshake.cancelled_by = user
    handshake.cancelled_at = timezone.now()
    handshake.save(update_fields=["status", "cancelled_by", "cancelled_at", "updated_at"])
    return handshake
