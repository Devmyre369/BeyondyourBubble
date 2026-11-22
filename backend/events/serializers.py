
import re

from rest_framework import serializers
from django.utils import timezone

from hubs.models import Hub

from .models import Event, EventModerationReview


class EventModerationHistorySerializer(serializers.ModelSerializer):
    reviewer_username = serializers.CharField(
        source="reviewer.username",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = EventModerationReview
        fields = [
            "id",
            "decision",
            "review_category",
            "review_notes",
            "reviewed_at",
            "reviewer_username",
        ]
        read_only_fields = fields


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

    Organiser contact details are collected for private BYB moderation
    and are never returned in the submission response.
    """

    hub_id = serializers.UUIDField(write_only=True)

    organiser_contact_name = serializers.CharField(
        max_length=150,
        required=True,
        trim_whitespace=True,
    )

    organiser_designation = serializers.CharField(
        max_length=100,
        required=True,
        trim_whitespace=True,
    )

    organiser_phone = serializers.CharField(
        max_length=20,
        required=True,
        trim_whitespace=True,
    )

    organiser_whatsapp = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )

    organiser_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        default="",
    )

    organiser_contact_consent = serializers.BooleanField(
        required=True,
    )

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
            "organiser_contact_name",
            "organiser_designation",
            "organiser_phone",
            "organiser_whatsapp",
            "organiser_email",
            "organiser_contact_consent",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "organiser_contact_name": {"write_only": True},
            "organiser_designation": {"write_only": True},
            "organiser_phone": {"write_only": True},
            "organiser_whatsapp": {"write_only": True},
            "organiser_email": {"write_only": True},
            "organiser_contact_consent": {"write_only": True},
        }

    @staticmethod
    def validate_phone_number(value):
        """
        Accepts international phone numbers with common formatting.

        The number must contain between 7 and 15 digits.
        """
        digits = re.sub(r"\D", "", value)

        if not 7 <= len(digits) <= 15:
            raise serializers.ValidationError(
                "Enter a valid phone number containing 7 to 15 digits."
            )

        if not re.fullmatch(r"\+?[0-9\s().-]+", value):
            raise serializers.ValidationError(
                "Use only digits, spaces, +, parentheses, dots or hyphens."
            )

        if "+" in value and not value.startswith("+"):
            raise serializers.ValidationError(
                "The + country-code prefix must appear at the beginning."
            )

        return value

    def validate_organiser_phone(self, value):
        return self.validate_phone_number(value)

    def validate_organiser_whatsapp(self, value):
        if not value:
            return value

        return self.validate_phone_number(value)

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

        if starts_at <= timezone.now():
            raise serializers.ValidationError({
                "starts_at": "New events must start in the future."
            })

        # Organiser contact verification requirements.
        if not attrs.get("organiser_contact_name", "").strip():
            raise serializers.ValidationError({
                "organiser_contact_name": "Organiser contact name is required."
            })

        if not attrs.get("organiser_designation", "").strip():
            raise serializers.ValidationError({
                "organiser_designation": "Organiser designation is required."
            })

        if not attrs.get("organiser_phone", "").strip():
            raise serializers.ValidationError({
                "organiser_phone": "Organiser phone number is required."
            })

        if attrs.get("organiser_contact_consent") is not True:
            raise serializers.ValidationError({
                "organiser_contact_consent": (
                    "Consent is required for BYB to contact the organiser "
                    "to verify the event."
                )
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

    Organiser contact details are deliberately excluded.
    Online joining details are only visible to eligible participants,
    Hub event managers, and BYB staff.
    """

    organising_hub_name = serializers.CharField(
        source="organising_hub.name",
        read_only=True,
    )

    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    is_registered = serializers.BooleanField(read_only=True)

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
            "is_registered",
            "organising_hub",
            "organising_hub_name",
            "created_by_username",
            "created_at",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")
        user = getattr(request, "user", None)

        private_access = bool(
            getattr(instance, "is_registered", False)
            or getattr(instance, "can_manage_event", False)
            or (user and user.is_authenticated and user.is_staff)
        )

        if not private_access:
            data.pop("online_join_url", None)
            data.pop("online_access_instructions", None)

        return data


class HubEventManagementSerializer(serializers.ModelSerializer):
    """
    Event details visible to eligible managers of its organising Hub.

    Organiser contact details remain restricted to BYB staff.
    """

    organising_hub_name = serializers.CharField(
        source="organising_hub.name",
        read_only=True,
    )

    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    reviewed_by_username = serializers.CharField(
        source="reviewed_by.username",
        read_only=True,
        allow_null=True,
    )

    moderation_history = EventModerationHistorySerializer(
        many=True,
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
            "moderation_status",
            "organising_hub",
            "organising_hub_name",
            "created_by",
            "created_by_username",
            "reviewed_by",
            "reviewed_by_username",
            "review_notes",
            "review_category",
            "reviewed_at",
            "created_at",
            "updated_at",
            "moderation_history",
        ]
        read_only_fields = fields


class EventUpdateSerializer(serializers.ModelSerializer):
    """
    Validates editable event information.

    Hub ownership, creator identity and moderation fields
    cannot be changed through this serializer.
    """

    class Meta:
        model = Event
        fields = [
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

    def validate(self, attrs):
        instance = self.instance

        starts_at = attrs.get(
            "starts_at",
            instance.starts_at if instance else None,
        )

        ends_at = attrs.get(
            "ends_at",
            instance.ends_at if instance else None,
        )

        event_format = attrs.get(
            "format",
            instance.format if instance else Event.Format.OFFLINE,
        )

        venue_name = attrs.get(
            "venue_name",
            instance.venue_name if instance else "",
        ).strip()

        venue_address = attrs.get(
            "venue_address",
            instance.venue_address if instance else "",
        ).strip()

        city = attrs.get(
            "city",
            instance.city if instance else "",
        ).strip()

        online_join_url = attrs.get(
            "online_join_url",
            instance.online_join_url if instance else "",
        ).strip()

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

        if (
            instance
            and "starts_at" in attrs
            and starts_at.replace(microsecond=0)
            != instance.starts_at.replace(microsecond=0)
            and starts_at <= timezone.now()
        ):
            raise serializers.ValidationError({
                "starts_at": "A rescheduled event must start in the future."
            })

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


class EventModerationQueueSerializer(serializers.ModelSerializer):
    """
    Event details shown to authorised BYB staff in the moderation queue.

    This is the only event serializer that exposes organiser contact data.
    The moderation endpoint must remain staff-protected.
    """

    organising_hub_name = serializers.CharField(
        source="organising_hub.name",
        read_only=True,
    )

    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    moderation_history = EventModerationHistorySerializer(
        many=True,
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
            "review_category",
            "review_notes",
            "moderation_history",

            # Private organiser contact information.
            "organiser_contact_name",
            "organiser_designation",
            "organiser_phone",
            "organiser_whatsapp",
            "organiser_email",
            "organiser_contact_consent",
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

    review_category = serializers.ChoiceField(
        choices=Event.RejectionCategory.choices,
        required=False,
        allow_blank=True,
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

        if (
            attrs["decision"] == "reject"
            and not attrs.get("review_category")
        ):
            raise serializers.ValidationError({
                "review_category": "Choose a rejection category."
            })

        if (
            attrs["decision"] == "approve"
            and attrs.get("review_category")
        ):
            raise serializers.ValidationError({
                "review_category": (
                    "Rejection categories are only valid for rejections."
                )
            })

        return attrs
