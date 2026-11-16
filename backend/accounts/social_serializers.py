from rest_framework import serializers

from accounts.models import User


class PublicConnectionUserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    byb_signature = serializers.SerializerMethodField()
    profile_type = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    institution = serializers.SerializerMethodField()
    current_organization = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    is_following = serializers.BooleanField(
        source="viewer_follows",
        read_only=True,
        default=False,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "profile_picture",
            "byb_signature",
            "profile_type",
            "bio",
            "city",
            "institution",
            "current_organization",
            "job_title",
            "is_following",
        ]
        read_only_fields = fields

    def get_profile_picture(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.profile_picture if profile else ""

    def get_byb_signature(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.byb_signature if profile else None

    def get_profile_type(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.profile_type if profile else None

    def get_bio(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.bio if profile else ""

    def get_city(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.city if profile else ""

    def get_institution(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.institution if profile else ""

    def get_current_organization(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.current_organization if profile else ""

    def get_job_title(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.job_title if profile else ""
