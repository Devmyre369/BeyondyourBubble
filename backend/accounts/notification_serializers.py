from rest_framework import serializers

from .models import Notification
from events.models import Event
from events.permissions import can_submit_hub_event


class NotificationSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username")
    actor_first_name = serializers.CharField(source="actor.first_name")
    actor_last_name = serializers.CharField(source="actor.last_name")
    actor_profile_picture = serializers.SerializerMethodField()
    vibe_id = serializers.UUIDField(read_only=True)
    moment_id = serializers.UUIDField(read_only=True)
    handshake_id = serializers.UUIDField(read_only=True, allow_null=True)
    handshake_status = serializers.CharField(
        source="handshake.status",
        read_only=True,
        allow_null=True,
    )
    event_id = serializers.SerializerMethodField()
    event_title = serializers.SerializerMethodField()
    event_status = serializers.SerializerMethodField()
    event_moderation_status = serializers.SerializerMethodField()
    hub_id = serializers.SerializerMethodField()
    hub_name = serializers.SerializerMethodField()
    content_author_username = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id",
            "verb",
            "actor_username",
            "actor_first_name",
            "actor_last_name",
            "actor_profile_picture",
            "vibe_id",
            "moment_id",
            "handshake_id",
            "handshake_status",
            "event_id",
            "event_title",
            "event_status",
            "event_moderation_status",
            "hub_id",
            "hub_name",
            "content_author_username",
            "created_at",
            "read_at",
        )

    def get_actor_profile_picture(self, notification):
        profile = getattr(notification.actor, "profile", None)
        if (
            profile
            and profile.visibility == "public"
        ):
            return profile.profile_picture
        return ""

    def _event_is_visible(self, notification):
        cache = getattr(self, "_event_visibility_cache", {})
        if notification.pk in cache:
            return cache[notification.pk]

        event = notification.event
        if event is None:
            cache[notification.pk] = False
            self._event_visibility_cache = cache
            return False
        if not event.organising_hub.is_active:
            cache[notification.pk] = False
            self._event_visibility_cache = cache
            return False
        if (
            event.status == Event.Status.PUBLISHED
            and event.moderation_status == Event.ModerationStatus.APPROVED
        ):
            cache[notification.pk] = True
            self._event_visibility_cache = cache
            return True
        request = self.context.get("request")
        if request is None:
            cache[notification.pk] = False
            self._event_visibility_cache = cache
            return False
        user = request.user
        visible = bool(
            user.is_staff
            or event.created_by_id == user.pk
            or can_submit_hub_event(user=user, hub=event.organising_hub)
        )
        cache[notification.pk] = visible
        self._event_visibility_cache = cache
        return visible

    def get_event_id(self, notification):
        return str(notification.event_id) if self._event_is_visible(notification) else None

    def get_event_title(self, notification):
        return notification.event.title if self._event_is_visible(notification) else None

    def get_event_status(self, notification):
        return notification.event.status if self._event_is_visible(notification) else None

    def get_event_moderation_status(self, notification):
        return notification.event.moderation_status if self._event_is_visible(notification) else None

    def get_hub_id(self, notification):
        if notification.hub_id:
            return str(notification.hub_id) if notification.hub.is_active else None
        if notification.event_id:
            hub = notification.event.organising_hub
            return str(hub.id) if hub.is_active else None
        return None

    def get_hub_name(self, notification):
        if notification.hub_id:
            return notification.hub.name if notification.hub.is_active else None
        if notification.event_id:
            hub = notification.event.organising_hub
            return hub.name if hub.is_active else None
        return None

    def get_content_author_username(self, notification):
        content = notification.vibe or notification.moment
        return content.author.username if content else None
