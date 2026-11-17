from accounts.models import Notification


def create_notification(actor, recipient, verb, vibe=None, moment=None):
    if actor.pk == recipient.pk:
        return None

    return Notification.objects.create(
        actor=actor,
        recipient=recipient,
        verb=verb,
        vibe=vibe,
        moment=moment,
    )
