
from django.db.models import Q

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Event
from .serializers import (
    EventChoiceSerializer,
    EventDiscoverySerializer,
    EventSubmissionSerializer,
    EventModerationQueueSerializer,
    EventModerationReviewSerializer,
)
from .services.moderation_service import review_event


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


class EventModerationQueueView(generics.ListAPIView):
    """
    List events awaiting BYB staff moderation.
    """

    serializer_class = EventModerationQueueSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Event.objects.filter(
            moderation_status=Event.ModerationStatus.PENDING,
            organising_hub__is_active=True,
        ).select_related(
            "organising_hub",
            "created_by",
        ).order_by("created_at")


class EventModerationReviewView(APIView):
    """
    Approve or reject a pending event.
    """

    permission_classes = [IsAdminUser]

    def post(self, request, event_id):
        serializer = EventModerationReviewSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        event = review_event(
            event_id=event_id,
            reviewer=request.user,
            decision=serializer.validated_data["decision"],
            review_notes=serializer.validated_data.get(
                "review_notes",
                "",
            ),
        )

        return Response({
            "message": (
                "Event approved and published."
                if event.moderation_status == Event.ModerationStatus.APPROVED
                else "Event rejected."
            ),
            "event_id": str(event.id),
            "status": event.status,
            "moderation_status": event.moderation_status,
            "review_notes": event.review_notes,
            "reviewed_at": event.reviewed_at,
        })
