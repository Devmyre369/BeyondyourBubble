from collections.abc import Mapping

from rest_framework import serializers

from .models import Hub
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
            "created_at",
        ]
        read_only_fields = fields


class HubDetailSerializer(serializers.ModelSerializer):
    can_edit = serializers.SerializerMethodField()
    can_edit_membership_policy = serializers.SerializerMethodField()

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
