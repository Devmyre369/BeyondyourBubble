from collections.abc import Mapping

from rest_framework import serializers

from accounts.models import Profile

from .models import Hub, HubApplication, HubMembership, HubVerificationRequest
from .permissions import can_edit_hub
from .services.hub_creation_service import create_hub


class HubCreateSerializer(serializers.ModelSerializer):
    visibility = serializers.ChoiceField(
        choices=Hub.Visibility.choices,
        required=False,
        default=Hub.Visibility.PUBLIC,
    )
    membership_policy = serializers.ChoiceField(
        choices=Hub.MembershipPolicy.choices,
        required=False,
        default=Hub.MembershipPolicy.APPROVAL_REQUIRED,
    )

    class Meta:
        model = Hub
        fields = [
            "name",
            "hub_type",
            "visibility",
            "membership_policy",
            "short_description",
            "description",
            "logo",
            "cover_image",
            "website",
            "contact_email",
            "city",
            "college_or_parent_organisation",
        ]

    def create(self, validated_data):
        creator = self.context["request"].user
        return create_hub(creator, validated_data)


class HubDiscoveryQuerySerializer(serializers.Serializer):
    search = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )
    hub_type = serializers.ChoiceField(
        choices=Hub.HubType.choices,
        required=False,
    )
    city = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )


class HubListSerializer(serializers.ModelSerializer):
    verification_status = serializers.SerializerMethodField()

    def get_verification_status(self, obj):
        return _verification_status(obj)

    class Meta:
        model = Hub
        fields = [
            "id",
            "name",
            "slug",
            "hub_type",
            "short_description",
            "logo",
            "cover_image",
            "city",
            "college_or_parent_organisation",
            "is_verified",
            "verification_status",
            "created_at",
        ]
        read_only_fields = fields


class HubDetailSerializer(serializers.ModelSerializer):
    can_edit = serializers.SerializerMethodField()
    can_edit_membership_policy = serializers.SerializerMethodField()
    verification_status = serializers.SerializerMethodField()
    can_request_verification = serializers.SerializerMethodField()
    verification_review_notes = serializers.SerializerMethodField()
    verification_reviewed_at = serializers.SerializerMethodField()

    class Meta:
        model = Hub
        fields = [
            "id",
            "name",
            "slug",
            "hub_type",
            "short_description",
            "description",
            "logo",
            "cover_image",
            "website",
            "city",
            "college_or_parent_organisation",
            "is_verified",
            "verification_status",
            "can_request_verification",
            "verification_review_notes",
            "verification_reviewed_at",
            "created_at",
            "membership_policy",
            "can_edit",
            "can_edit_membership_policy",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj):
        request = self.context.get("request")
        return bool(request and can_edit_hub(request.user, obj))

    def get_can_edit_membership_policy(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and obj.owner_id == request.user.pk
        )

    def _latest_verification(self, obj):
        return obj.verification_requests.order_by("-requested_at").first()

    def get_verification_status(self, obj):
        return _verification_status(obj)

    def get_can_request_verification(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        if obj.owner_id != request.user.pk or not obj.is_active or obj.is_verified:
            return False
        return _verification_status(obj) != HubVerificationRequest.Status.PENDING

    def get_verification_review_notes(self, obj):
        request = self.context.get("request")
        can_see_notes = bool(
            request
            and request.user.is_authenticated
            and (obj.owner_id == request.user.pk or request.user.is_staff)
        )
        latest = self._latest_verification(obj) if can_see_notes else None
        return latest.review_notes if latest else ""

    def get_verification_reviewed_at(self, obj):
        request = self.context.get("request")
        can_see_review = bool(
            request
            and request.user.is_authenticated
            and (obj.owner_id == request.user.pk or request.user.is_staff)
        )
        latest = self._latest_verification(obj) if can_see_review else None
        return latest.reviewed_at if latest else None


def _verification_status(hub):
    if hub.is_verified:
        return HubVerificationRequest.Status.APPROVED
    latest = hub.verification_requests.order_by("-requested_at").first()
    return latest.status if latest else "not_requested"


class StrictInputSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown_fields = set(data.keys()) - set(self.fields.keys())
            if unknown_fields:
                raise serializers.ValidationError({
                    field: ["This field may not be modified."]
                    for field in sorted(unknown_fields)
                })
        return super().to_internal_value(data)


class HubApplicationSubmitSerializer(StrictInputSerializer):
    requested_name = serializers.CharField(max_length=200, trim_whitespace=True)
    requested_slug = serializers.SlugField(max_length=200)
    hub_type = serializers.ChoiceField(choices=Hub.HubType.choices)
    organisation_description = serializers.CharField(required=False, allow_blank=True, max_length=10000)
    college_or_parent_organisation = serializers.CharField(required=False, allow_blank=True, max_length=200)
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    website = serializers.URLField(required=False, allow_blank=True, max_length=500)
    contact_email = serializers.EmailField(required=False, allow_blank=True)

    def validate_requested_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("A Hub name is required.")
        return value.strip()

    def validate_requested_slug(self, value):
        value = value.strip().lower()
        if Hub.objects.filter(slug=value).exists():
            raise serializers.ValidationError("A Hub already uses this slug.")
        if HubApplication.objects.filter(
            requested_slug=value,
            status=HubApplication.Status.PENDING,
        ).exists():
            raise serializers.ValidationError(
                "A pending Hub application already uses this slug."
            )
        return value

    def validate(self, attrs):
        applicant = self.context["request"].user
        if HubApplication.objects.filter(
            applicant=applicant,
            requested_slug=attrs["requested_slug"],
            status=HubApplication.Status.PENDING,
        ).exists():
            raise serializers.ValidationError(
                "You already have a pending application for this organisation."
            )
        if HubApplication.objects.filter(
            applicant=applicant,
            requested_slug=attrs["requested_slug"],
            status=HubApplication.Status.APPROVED,
        ).exists():
            raise serializers.ValidationError("This application has already been approved.")
        return attrs


class HubApplicationSerializer(serializers.ModelSerializer):
    applicant_username = serializers.CharField(source="applicant.username", read_only=True)
    reviewer_username = serializers.CharField(source="reviewer.username", read_only=True, allow_null=True)
    created_hub_id = serializers.SerializerMethodField()

    class Meta:
        model = HubApplication
        fields = [
            "id", "requested_name", "requested_slug", "hub_type",
            "organisation_description", "college_or_parent_organisation",
            "city", "website", "contact_email", "status", "applicant",
            "applicant_username", "reviewer", "reviewer_username",
            "review_notes", "created_at", "updated_at", "reviewed_at",
            "created_hub_id",
        ]
        read_only_fields = fields

    def get_created_hub_id(self, obj):
        hub = Hub.objects.filter(slug=obj.requested_slug, created_by=obj.applicant).only("id").first()
        return str(hub.id) if hub else None


class HubApplicationReviewInputSerializer(StrictInputSerializer):
    decision = serializers.ChoiceField(choices=["approve", "reject"])
    review_notes = serializers.CharField(required=False, allow_blank=True, max_length=5000)

    def validate(self, attrs):
        if attrs["decision"] == "reject" and not attrs.get("review_notes", "").strip():
            raise serializers.ValidationError({
                "review_notes": "A reason is required when rejecting an application."
            })
        return attrs


class HubReviewQueueQuerySerializer(StrictInputSerializer):
    status = serializers.ChoiceField(choices=HubApplication.Status.choices, required=False)


class HubVerificationRequestInputSerializer(StrictInputSerializer):
    request_notes = serializers.CharField(required=False, allow_blank=True, max_length=5000)


class HubVerificationReviewInputSerializer(StrictInputSerializer):
    decision = serializers.ChoiceField(choices=["approve", "reject"])
    review_notes = serializers.CharField(required=False, allow_blank=True, max_length=5000)

    def validate(self, attrs):
        if attrs["decision"] == "reject" and not attrs.get("review_notes", "").strip():
            raise serializers.ValidationError({
                "review_notes": "A reason is required when rejecting verification."
            })
        return attrs


class HubVerificationRequestSerializer(serializers.ModelSerializer):
    hub_name = serializers.CharField(source="hub.name", read_only=True)
    hub_slug = serializers.CharField(source="hub.slug", read_only=True)
    hub_type = serializers.CharField(source="hub.hub_type", read_only=True)
    hub_city = serializers.CharField(source="hub.city", read_only=True)
    hub_is_verified = serializers.BooleanField(source="hub.is_verified", read_only=True)
    requested_by_username = serializers.CharField(source="requested_by.username", read_only=True)
    reviewer_username = serializers.CharField(source="reviewer.username", read_only=True, allow_null=True)

    class Meta:
        model = HubVerificationRequest
        fields = [
            "id", "hub", "hub_name", "hub_slug", "hub_type", "hub_city",
            "hub_is_verified", "requested_by", "requested_by_username",
            "request_notes", "status", "reviewer", "reviewer_username",
            "review_notes", "requested_at", "reviewed_at",
        ]
        read_only_fields = fields


class HubUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hub
        fields = [
            "name",
            "hub_type",
            "short_description",
            "description",
            "logo",
            "cover_image",
            "website",
            "city",
            "college_or_parent_organisation",
            "membership_policy",
        ]

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown_fields = set(data.keys()) - set(self.fields.keys())
            if unknown_fields:
                raise serializers.ValidationError({
                    field: ["This field may not be modified."]
                    for field in sorted(unknown_fields)
                })
        return super().to_internal_value(data)


class HubMembershipStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HubMembership
        fields = ["id", "role", "status", "joined_at"]
        read_only_fields = fields


class HubMemberSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = HubMembership
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "profile_picture",
            "role",
            "status",
            "joined_at",
        ]
        read_only_fields = fields

    def _public_profile(self, obj):
        user = obj.user
        if not user.is_active or not user.email_verified:
            return None
        profile = getattr(user, "profile", None)
        if profile is None:
            return None
        if profile.visibility != Profile.Visibility.PUBLIC:
            return None
        return profile

    def get_username(self, obj):
        if self._public_profile(obj):
            return obj.user.username
        return None

    def get_first_name(self, obj):
        if self._public_profile(obj):
            return obj.user.first_name
        return ""

    def get_last_name(self, obj):
        if self._public_profile(obj):
            return obj.user.last_name
        return ""

    def get_profile_picture(self, obj):
        profile = self._public_profile(obj)
        return profile.profile_picture if profile else ""


class StrictMembershipInputSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown_fields = set(data.keys()) - set(self.fields.keys())
            if unknown_fields:
                raise serializers.ValidationError({
                    field: ["This field may not be modified."]
                    for field in sorted(unknown_fields)
                })
        return super().to_internal_value(data)


class HubInviteSerializer(StrictMembershipInputSerializer):
    username = serializers.CharField(
        max_length=150,
        trim_whitespace=True,
    )


class HubMemberRoleSerializer(StrictMembershipInputSerializer):
    role = serializers.ChoiceField(
        choices=[
            HubMembership.Role.ADMIN,
            HubMembership.Role.EDITOR,
            HubMembership.Role.MEMBER,
        ],
    )
