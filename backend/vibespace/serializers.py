
from rest_framework import serializers

from events.models import Event
from .models import Vibe, Moment


class EventAssociationValidationMixin:

    def validate_event(self, event):
        if event is None:
            return None

        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required to associate content with an event."
            )

        if event.organiser_id != request.user.id:
            raise serializers.ValidationError(
                "Only the event organiser can currently associate content "
                "with this event. Attendee access will be supported later."
            )

        return event


class VibeSerializer(
    EventAssociationValidationMixin,
    serializers.ModelSerializer
):

    author_username = serializers.CharField(
        source="author.username",
        read_only=True
    )

    event_title = serializers.CharField(
        source="event.title",
        read_only=True,
        allow_null=True
    )

    event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.filter(
            status__in=[
                Event.Status.PUBLISHED,
                Event.Status.COMPLETED,
            ]
        ),
        required=False,
        allow_null=True
    )

    text = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
        allow_blank=False
    )

    class Meta:
        model = Vibe

        fields = [
            "id",
            "author_username",
            "event",
            "event_title",
            "text",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "author_username",
            "event_title",
            "created_at",
            "updated_at",
        ]


class MomentSerializer(
    EventAssociationValidationMixin,
    serializers.ModelSerializer
):

    author_username = serializers.CharField(
        source="author.username",
        read_only=True
    )

    event_title = serializers.CharField(
        source="event.title",
        read_only=True,
        allow_null=True
    )

    event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.filter(
            status__in=[
                Event.Status.PUBLISHED,
                Event.Status.COMPLETED,
            ]
        ),
        required=False,
        allow_null=True
    )

    caption = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        trim_whitespace=True
    )

    image_url = serializers.URLField(read_only=True)

    class Meta:
        model = Moment

        fields = [
            "id",
            "author_username",
            "event",
            "event_title",
            "image_url",
            "caption",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "author_username",
            "event_title",
            "image_url",
            "created_at",
            "updated_at",
        ]
