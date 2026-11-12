from rest_framework import serializers

from .models import Event


class EventChoiceSerializer(serializers.ModelSerializer):

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