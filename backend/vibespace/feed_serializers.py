
from rest_framework import serializers


class FeedEntrySerializer(serializers.Serializer):
    """
    Standard response structure for both Vibes and Moments.
    """

    id = serializers.UUIDField(read_only=True)

    content_type = serializers.ChoiceField(
        choices=["vibe", "moment"],
        read_only=True,
    )

    author_username = serializers.CharField(read_only=True)

    author_profile_picture = serializers.CharField(
        read_only=True,
        allow_blank=True,
    )

    event_id = serializers.UUIDField(
        read_only=True,
        allow_null=True,
    )

    event_title = serializers.CharField(
        read_only=True,
        allow_null=True,
    )

    content_text = serializers.CharField(
        read_only=True,
        allow_blank=True,
    )

    image_url = serializers.CharField(
        read_only=True,
        allow_blank=True,
    )

    created_at = serializers.DateTimeField(read_only=True)
