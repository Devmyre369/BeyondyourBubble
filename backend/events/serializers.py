
from rest_framework import serializers

from hubs.models import Hub

from .models import Event


class EventChoiceSerializer(serializers.ModelSerializer):
    """
    Events available for association with VibeSpace content.
    """

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "starts_at",
            "venue_name",
            "city",
            "status",
        ]
        read_only_fields = fields


class EventSubmissionSerializer(serializers.ModelSerializer):
    """
    Validates event submissions made on behalf of a BYB Hub.
    """

    hub_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "hub_id",
            "title",
            "description",
            "category",
            "cover_image_url",
            "starts_at",
            "ends_at",
            "format",
            "venue_name",
            "venue_address",
            "city",
            "online_join_url",
            "online_access_instructions",
        ]
        read_only_fields = ["id"]

    def validate_hub_id(self, value):
        try:
            hub = Hub.objects.get(
                id=value,
                is_active=True,
            )
        except Hub.DoesNotExist:
            raise serializers.ValidationError(
                "The selected Hub does not exist or is inactive."
            )

        self.context["organising_hub"] = hub
        return value

    def validate(self, attrs):
        starts_at = attrs.get("starts_at")
        ends_at = attrs.get("ends_at")
        event_format = attrs.get("format")

        if not starts_at:
            raise serializers.ValidationError({
                "starts_at": "Event start date and time are required."
            })

        if not ends_at:
            raise serializers.ValidationError({
                "ends_at": "Event end date and time are required."
            })

        if ends_at <= starts_at:
            raise serializers.ValidationError({
                "ends_at": "Event end must be after its start."
            })

        venue_name = attrs.get("venue_name", "").strip()
        venue_address = attrs.get("venue_address", "").strip()
        city = attrs.get("city", "").strip()
        online_join_url = attrs.get("online_join_url", "").strip()

        if event_format in [
            Event.Format.OFFLINE,
            Event.Format.HYBRID,
        ]:
            missing_fields = {}

            if not venue_name:
                missing_fields["venue_name"] = (
                    "Venue name is required for offline and hybrid events."
                )

            if not venue_address:
                missing_fields["venue_address"] = (
                    "Venue address is required for offline and hybrid events."
                )

            if not city:
                missing_fields["city"] = (
                    "City is required for offline and hybrid events."
                )

            if missing_fields:
                raise serializers.ValidationError(missing_fields)

        if event_format in [
            Event.Format.ONLINE,
            Event.Format.HYBRID,
        ]:
            if not online_join_url:
                raise serializers.ValidationError({
                    "online_join_url": (
                        "An online joining URL is required "
                        "for online and hybrid events."
                    )
                })

        return attrs

    def create(self, validated_data):
        from events.services.event_service import create_event

        validated_data.pop("hub_id")

        return create_event(
            hub=self.context["organising_hub"],
            user=self.context["request"].user,
            validated_data=validated_data,
        )


class EventDiscoverySerializer(serializers.ModelSerializer):
    """
    Public representation of an approved event.
    Online joining details are publicly visible in V1.
    """

    organising_hub_name = serializers.CharField(
        source="organising_hub.name",
        read_only=True,
    )

    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "category",
            "cover_image_url",
            "starts_at",
            "ends_at",
            "format",
            "venue_name",
            "venue_address",
            "city",
            "online_join_url",
            "online_access_instructions",
            "status",
            "organising_hub",
            "organising_hub_name",
            "created_by_username",
            "created_at",
        ]
        read_only_fields = fields



class EventModerationQueueSerializer(serializers.ModelSerializer):
    """
    Event details shown to BYB staff in the moderation queue.
    """

    organising_hub_name = serializers.CharField(
        source="organising_hub.name",
        read_only=True,
    )

    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "category",
            "cover_image_url",
            "starts_at",
            "ends_at",
            "format",
            "venue_name",
            "venue_address",
            "city",
            "online_join_url",
            "online_access_instructions",
            "organising_hub",
            "organising_hub_name",
            "created_by",
            "created_by_username",
            "created_at",
        ]
        read_only_fields = fields


class EventModerationReviewSerializer(serializers.Serializer):
    """
    Validates a staff member's moderation decision.
    """

    decision = serializers.ChoiceField(
        choices=[
            ("approve", "Approve"),
            ("reject", "Reject"),
        ]
    )

    review_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
    )

    def validate(self, attrs):
        if (
            attrs["decision"] == "reject"
            and not attrs.get("review_notes", "").strip()
        ):
            raise serializers.ValidationError({
                "review_notes": (
                    "Please provide a reason when rejecting an event."
                )
            })

        return attrs
