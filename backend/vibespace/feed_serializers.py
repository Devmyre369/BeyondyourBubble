
from rest_framework import serializers


class FeedEntrySerializer(serializers.Serializer):
    """
    Shared response structure for Vibes, Moments, and Events.
    """

    id = serializers.UUIDField(read_only=True)

    content_type = serializers.ChoiceField(
        choices=["vibe", "moment", "event"],
        read_only=True,
    )

    author_username = serializers.CharField(read_only=True)
    author_first_name = serializers.CharField(read_only=True)
    author_last_name = serializers.CharField(read_only=True)

    author_profile_picture = serializers.CharField(
        read_only=True,
        allow_blank=True,
    )

    author_byb_signature = serializers.CharField(
        read_only=True,
        allow_null=True,
    )

    is_following = serializers.BooleanField(read_only=True)

    event_id = serializers.UUIDField(
        read_only=True,
        allow_null=True,
    )

    event_title = serializers.CharField(
        read_only=True,
        allow_null=True,
    )

    event_hub_id = serializers.UUIDField(read_only=True, allow_null=True)
    event_hub_name = serializers.CharField(read_only=True, allow_null=True)
    event_cover_image_url = serializers.CharField(read_only=True, allow_blank=True)
    event_starts_at = serializers.DateTimeField(read_only=True, allow_null=True)
    event_venue = serializers.CharField(read_only=True, allow_blank=True)
    event_city = serializers.CharField(read_only=True, allow_blank=True)
    event_category = serializers.CharField(read_only=True, allow_blank=True)
    event_format = serializers.CharField(read_only=True, allow_blank=True)

    content_text = serializers.CharField(
        read_only=True,
        allow_blank=True,
    )

    image_url = serializers.CharField(
        read_only=True,
        allow_blank=True,
    )

    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    revibe_count = serializers.IntegerField(read_only=True)
    save_count = serializers.IntegerField(read_only=True)
    share_count = serializers.IntegerField(read_only=True)

    created_at = serializers.DateTimeField(read_only=True)
