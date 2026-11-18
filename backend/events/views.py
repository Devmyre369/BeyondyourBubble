
from django.db.models import Q

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Event
from .serializers import (
    EventChoiceSerializer,
    EventDiscoverySerializer,
    EventSubmissionSerializer,
)


class EventDiscoveryListCreateView(generics.ListCreateAPIView):
    """
    GET: Discover approved and published events.
    POST: Submit an event through an eligible Hub.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Event.objects.filter(
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.APPROVED,
            organising_hub__is_active=True,
        ).select_related(
            "organising_hub",
            "created_by",
        )

        search = self.request.query_params.get("search")
        category = self.request.query_params.get("category")
        city = self.request.query_params.get("city")
        event_format = self.request.query_params.get("format")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(venue_name__icontains=search)
                | Q(city__icontains=search)
            )

        if category:
            queryset = queryset.filter(category=category)

        if city:
            queryset = queryset.filter(city__icontains=city)

        if event_format:
            queryset = queryset.filter(format=event_format)

        return queryset.order_by("starts_at", "-created_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EventSubmissionSerializer

        return EventDiscoverySerializer


class EventDiscoveryDetailView(generics.RetrieveAPIView):
    """
    Retrieve an approved and published event.
    """

    serializer_class = EventDiscoverySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Event.objects.filter(
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.APPROVED,
            organising_hub__is_active=True,
        ).select_related(
            "organising_hub",
            "created_by",
        )


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
