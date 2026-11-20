
from django.db.models import Q

from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from hubs.models import Hub

from .models import Event
from .pagination import EventPagination
from .permissions import can_submit_hub_event
from .serializers import (
    EventChoiceSerializer,
    EventDiscoverySerializer,
    EventSubmissionSerializer,
    EventModerationQueueSerializer,
    EventModerationReviewSerializer,
    HubEventManagementSerializer,
    EventUpdateSerializer,
)
from .services.event_service import update_event, cancel_event
from .services.moderation_service import review_event
from .services.event_image_service import EventImageError, upload_event_cover_image


class EventDiscoveryListCreateView(generics.ListCreateAPIView):
    """
    GET: Discover approved and published events.
    POST: Submit an event through an eligible Hub.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = EventPagination

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
    Return approved events created by the authenticated user.
    Used by VibeSpace for event association.
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


class HubEventManagementListView(generics.ListAPIView):
    """
    List all events belonging to a Hub.

    Only approved Hub owners, admins and editors can access it.
    Includes pending, rejected, published, cancelled and completed events.
    """

    serializer_class = HubEventManagementSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = EventPagination

    def get_queryset(self):
        hub_id = self.kwargs["hub_id"]

        try:
            hub = Hub.objects.get(
                id=hub_id,
                is_active=True,
            )
        except Hub.DoesNotExist:
            raise NotFound("Hub not found.")

        if not can_submit_hub_event(
            user=self.request.user,
            hub=hub,
        ):
            raise PermissionDenied(
                "Only approved Hub owners, administrators and editors "
                "can manage this Hub's events."
            )

        return Event.objects.filter(
            organising_hub=hub,
        ).select_related(
            "organising_hub",
            "created_by",
            "reviewed_by",
        ).order_by("-created_at")


class EventManagementDetailView(APIView):
    """
    Retrieve or update an event belonging to a Hub.

    GET: Retrieve event management details.
    PUT: Full update.
    PATCH: Partial update.
    """

    permission_classes = [IsAuthenticated]

    def get_event(self, event_id, user):
        event = (
            Event.objects
            .select_related("organising_hub")
            .filter(
                id=event_id,
                organising_hub__is_active=True,
            )
            .first()
        )

        if event is None:
            raise NotFound("Event not found.")

        if not can_submit_hub_event(
            user=user,
            hub=event.organising_hub,
        ):
            raise PermissionDenied(
                "You do not have permission to manage this Hub event."
            )

        return event

    def get(self, request, event_id):
        event = self.get_event(event_id, request.user)

        serializer = HubEventManagementSerializer(event)

        return Response(serializer.data)

    def put(self, request, event_id):
        return self.update(request, event_id, partial=False)

    def patch(self, request, event_id):
        return self.update(request, event_id, partial=True)

    def update(self, request, event_id, partial):
        event = self.get_event(event_id, request.user)

        serializer = EventUpdateSerializer(
            event,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)

        updated_event = update_event(
            event_id=event.id,
            user=request.user,
            validated_data=serializer.validated_data,
        )

        return Response(
            HubEventManagementSerializer(updated_event).data
        )


class EventManagementCancelView(APIView):
    """
    Cancel a published event belonging to a Hub.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        event = cancel_event(
            event_id=event_id,
            user=request.user,
        )

        return Response({
            "message": "Event cancelled successfully.",
            "event_id": str(event.id),
            "status": event.status,
            "moderation_status": event.moderation_status,
        })


class EventModerationQueueView(generics.ListAPIView):
    """
    List events awaiting BYB staff moderation.
    """

    serializer_class = EventModerationQueueSerializer
    permission_classes = [IsAdminUser]
    pagination_class = EventPagination

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


class EventCoverImageUploadView(APIView):
    """
    Upload a cover image for an existing event.

    POST /events/manage/<event_id>/cover-image/
    Accepts a multipart/form-data request with an "image" file field.
    Returns the updated managed event representation.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, event_id):
        event = (
            Event.objects
            .select_related("organising_hub")
            .filter(
                id=event_id,
                organising_hub__is_active=True,
            )
            .first()
        )

        if event is None:
            raise NotFound("Event not found.")

        if not can_submit_hub_event(user=request.user, hub=event.organising_hub):
            raise PermissionDenied(
                "You do not have permission to manage this Hub event."
            )

        uploaded_file = request.FILES.get("image")

        if not uploaded_file:
            return Response(
                {
                    "success": False,
                    "message": "Please select an image to upload.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            image_url = upload_event_cover_image(
                event_id=event.id,
                uploaded_file=uploaded_file,
            )
        except EventImageError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        event.cover_image_url = image_url
        event.save(update_fields=["cover_image_url"])

        return Response(
            {
                "success": True,
                "message": "Cover image uploaded successfully.",
                "cover_image_url": image_url,
                "event": HubEventManagementSerializer(event).data,
            },
            status=status.HTTP_200_OK,
        )
