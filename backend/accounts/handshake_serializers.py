from rest_framework import serializers

from accounts.models import Handshake, Profile


class HandshakeItemSerializer(serializers.ModelSerializer):
    person = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()

    class Meta:
        model = Handshake
        fields = (
            "id",
            "status",
            "direction",
            "person",
            "created_at",
            "responded_at",
            "cancelled_at",
        )
        read_only_fields = fields

    def get_person(self, obj):
        viewer = self.context["request"].user
        person = obj.requester if obj.recipient_id == viewer.pk else obj.recipient
        profile = getattr(person, "profile", None)
        is_public = bool(
            profile
            and profile.visibility == Profile.Visibility.PUBLIC
            and person.is_active
            and person.email_verified
        )
        return {
            "id": str(person.pk),
            "username": person.username,
            "first_name": person.first_name if is_public else "",
            "last_name": person.last_name if is_public else "",
            "profile_picture": (
                profile.profile_picture
                if is_public and profile.profile_picture
                else ""
            ),
            "byb_signature": profile.byb_signature if is_public else None,
        }

    def get_direction(self, obj):
        return "incoming" if obj.recipient_id == self.context["request"].user.pk else "outgoing"
