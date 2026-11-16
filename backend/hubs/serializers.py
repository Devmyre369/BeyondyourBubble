from rest_framework import serializers

from .models import Hub
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
        ]
        read_only_fields = fields
