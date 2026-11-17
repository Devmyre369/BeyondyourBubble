from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username")
    actor_first_name = serializers.CharField(source="actor.first_name")
    actor_last_name = serializers.CharField(source="actor.last_name")
    actor_profile_picture = serializers.SerializerMethodField()
    vibe_id = serializers.UUIDField(read_only=True)
    moment_id = serializers.UUIDField(read_only=True)

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
            "created_at",
            "read_at",
        )

    def get_actor_profile_picture(self, notification):
        profile = getattr(notification.actor, "profile", None)
        return profile.profile_picture if profile else ""
