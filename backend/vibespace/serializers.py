
from rest_framework import serializers

from events.models import Event
from .models import (
    Vibe,
    Moment,
    Comment,
    Revibe,
    SavedContent,
)


class InteractionCountSerializerMixin:
    def get_count(self, obj, annotation, related_name):
        count = getattr(obj, annotation, None)
        if count is not None:
            return count
        return getattr(obj, related_name).count()

    def get_like_count(self, obj):
        return self.get_count(obj, "like_count", "likes")

    def get_comment_count(self, obj):
        return self.get_count(obj, "comment_count", "comments")

    def get_revibe_count(self, obj):
        return self.get_count(obj, "revibe_count", "revibes")

    def get_save_count(self, obj):
        return self.get_count(obj, "save_count", "saved_by")

    def get_share_count(self, obj):
        return self.get_count(obj, "share_count", "shares")


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
    InteractionCountSerializerMixin,
    serializers.ModelSerializer
):
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    revibe_count = serializers.SerializerMethodField()
    save_count = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()

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
            "like_count",
            "comment_count",
            "revibe_count",
            "save_count",
            "share_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author_username",
            "event_title",
            "like_count",
            "comment_count",
            "revibe_count",
            "save_count",
            "share_count",
            "created_at",
            "updated_at",
        ]


class MomentSerializer(
    EventAssociationValidationMixin,
    InteractionCountSerializerMixin,
    serializers.ModelSerializer
):
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    revibe_count = serializers.SerializerMethodField()
    save_count = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()

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
            "like_count",
            "comment_count",
            "revibe_count",
            "save_count",
            "share_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author_username",
            "event_title",
            "image_url",
            "like_count",
            "comment_count",
            "revibe_count",
            "save_count",
            "share_count",
            "created_at",
            "updated_at",
        ]


# ==================================================
# COMMENT SERIALIZER
# ==================================================

class CommentSerializer(serializers.ModelSerializer):

    author_username = serializers.CharField(
        source="author.username",
        read_only=True
    )

    text = serializers.CharField(
        max_length=1000,
        trim_whitespace=True,
        allow_blank=False
    )

    class Meta:
        model = Comment
        fields = [
            "id",
            "author_username",
            "text",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author_username",
            "created_at",
            "updated_at",
        ]


# ==================================================
# REVIBE SERIALIZER
# ==================================================

class RevibeSerializer(serializers.ModelSerializer):

    author_username = serializers.CharField(
        source="author.username",
        read_only=True
    )

    vibe = serializers.PrimaryKeyRelatedField(read_only=True)
    moment = serializers.PrimaryKeyRelatedField(read_only=True)

    quote_text = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        trim_whitespace=True
    )

    class Meta:
        model = Revibe
        fields = [
            "id",
            "author_username",
            "vibe",
            "moment",
            "revibe_type",
            "quote_text",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "author_username",
            "vibe",
            "moment",
            "created_at",
        ]

    def validate(self, attrs):
        revibe_type = attrs.get(
            "revibe_type",
            getattr(
                self.instance,
                "revibe_type",
                Revibe.RevibeType.DIRECT
            )
        )

        quote_text = attrs.get(
            "quote_text",
            getattr(self.instance, "quote_text", "")
        )

        if revibe_type == Revibe.RevibeType.DIRECT and quote_text:
            raise serializers.ValidationError({
                "quote_text": "Direct Revibes cannot contain additional text."
            })

        if revibe_type == Revibe.RevibeType.QUOTE and not quote_text.strip():
            raise serializers.ValidationError({
                "quote_text": "Quote Revibes must contain additional text."
            })

        return attrs


# ==================================================
# SAVED CONTENT SERIALIZER
# ==================================================

class SavedContentSerializer(serializers.ModelSerializer):

    vibe = serializers.PrimaryKeyRelatedField(
        queryset=Vibe.objects.all(),
        required=False,
        allow_null=True
    )

    moment = serializers.PrimaryKeyRelatedField(
        queryset=Moment.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = SavedContent
        fields = [
            "id",
            "vibe",
            "moment",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate(self, attrs):
        vibe = attrs.get("vibe")
        moment = attrs.get("moment")

        if (vibe is None) == (moment is None):
            raise serializers.ValidationError(
                "Select exactly one Vibe or Moment to save."
            )

        return attrs
