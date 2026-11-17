
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Event
from .serializers import EventChoiceSerializer


class EventChoiceListView(generics.ListAPIView):
    """
    Return events created by the authenticated user.

    Used by VibeSpace when associating Vibes and Moments
    with an event.
    """

    serializer_class = EventChoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(
            created_by=self.request.user,
            status__in=[
                Event.Status.PUBLISHED,
                Event.Status.COMPLETED,
            ],
            moderation_status=Event.ModerationStatus.APPROVED,
        ).order_by("-starts_at", "-created_at")
