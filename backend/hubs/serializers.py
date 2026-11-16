from rest_framework import serializers

from .models import Hub


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
