
import uuid

from django.db import transaction
from django.db.models import BooleanField, Exists, OuterRef, Q, Value
from django.utils.dateparse import parse_date
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from hubs.models import Hub
from hubs.models import HubMembership

from .models import Event, EventRegistration
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

    permission_classes = [AllowAny]
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

        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_registered=Exists(EventRegistration.objects.filter(
                    event_id=OuterRef("pk"), user=user,
                    status=EventRegistration.Status.REGISTERED,
                )),
                can_manage_event=Exists(HubMembership.objects.filter(
                    hub_id=OuterRef("organising_hub_id"),
                    user=user,
                    status=HubMembership.Status.APPROVED,
                    role__in=(
                        HubMembership.Role.OWNER,
                        HubMembership.Role.ADMIN,
                        HubMembership.Role.EDITOR,
                    ),
                )),
            )
        else:
            queryset = queryset.annotate(
                is_registered=Value(False, output_field=BooleanField()),
                can_manage_event=Value(False, output_field=BooleanField()),
            )

        search = self.request.query_params.get("search")
        category = self.request.query_params.get("category")
        city = self.request.query_params.get("city")
        event_format = self.request.query_params.get("format")
        hub_id = self.request.query_params.get("hub_id")
        upcoming = self.request.query_params.get("upcoming")

        if hub_id:
            queryset = queryset.filter(organising_hub_id=hub_id)
        if upcoming in ("1", "true", "yes"):
            queryset = queryset.filter(starts_at__gte=timezone.now())

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

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]


class EventDiscoveryDetailView(generics.RetrieveAPIView):
    """
    Retrieve an approved and published event.
    """

    serializer_class = EventDiscoverySerializer
    permission_classes = [AllowAny]
    lookup_field = "id"

    def get_queryset(self):
        queryset = Event.objects.filter(
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.APPROVED,
            organising_hub__is_active=True,
        ).select_related(
            "organising_hub",
            "created_by",
        )
        user = self.request.user
        if user.is_authenticated:
            return queryset.annotate(
                is_registered=Exists(EventRegistration.objects.filter(
                    event_id=OuterRef("pk"), user=user,
                    status=EventRegistration.Status.REGISTERED,
                )),
                can_manage_event=Exists(HubMembership.objects.filter(
                    hub_id=OuterRef("organising_hub_id"),
                    user=user,
                    status=HubMembership.Status.APPROVED,
                    role__in=(HubMembership.Role.OWNER, HubMembership.Role.ADMIN, HubMembership.Role.EDITOR),
                )),
            )
        return queryset.annotate(
            is_registered=Value(False, output_field=BooleanField()),
            can_manage_event=Value(False, output_field=BooleanField()),
        )


class EventRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def get_event(self, event_id):
        event = Event.objects.filter(
            id=event_id,
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.APPROVED,
            organising_hub__is_active=True,
        ).first()
        if event is None:
            raise NotFound("Event not found.")
        return event

    def get(self, request, event_id):
        event = self.get_event(event_id)
        registered = EventRegistration.objects.filter(
            event=event, user=request.user,
            status=EventRegistration.Status.REGISTERED,
        ).exists()
        return Response({"event_id": str(event.id), "is_registered": registered})

    def post(self, request, event_id):
        event = self.get_event(event_id)
        if (
            not event.starts_at
            or event.starts_at <= timezone.now()
            or (event.ends_at and event.ends_at <= timezone.now())
        ):
            return Response({"detail": "Registration is closed for this event."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            registration, created = EventRegistration.objects.get_or_create(
                event=event, user=request.user,
                defaults={"status": EventRegistration.Status.REGISTERED},
            )
            if not created and registration.status != EventRegistration.Status.REGISTERED:
                registration.status = EventRegistration.Status.REGISTERED
                registration.save(update_fields=["status", "updated_at"])
        return Response({"event_id": str(event.id), "is_registered": True}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, event_id):
        event = self.get_event(event_id)
        EventRegistration.objects.filter(
            event=event, user=request.user,
            status=EventRegistration.Status.REGISTERED,
        ).update(status=EventRegistration.Status.CANCELLED, updated_at=timezone.now())
        return Response({"event_id": str(event.id), "is_registered": False})


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
        ).prefetch_related(
            "moderation_history__reviewer",
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
        queryset = Event.objects.filter(
            moderation_status=Event.ModerationStatus.PENDING,
            organising_hub__is_active=True,
        ).select_related(
            "organising_hub",
            "created_by",
        )
        params = self.request.query_params
        search = params.get("search", "").strip()
        category = params.get("category")
        event_format = params.get("format")
        city = params.get("city", "").strip()
        hub_id = params.get("hub_id")
        hub = params.get("hub", "").strip()
        submitted_after = params.get("submitted_after")
        submitted_before = params.get("submitted_before")

        if search:
            queryset = queryset.filter(title__icontains=search)
        if category:
            queryset = queryset.filter(category=category)
        if event_format:
            queryset = queryset.filter(format=event_format)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if hub_id:
            queryset = queryset.filter(organising_hub_id=hub_id)
        if hub:
            try:
                hub_uuid = uuid.UUID(hub)
            except ValueError:
                queryset = queryset.filter(
                    Q(organising_hub__name__icontains=hub)
                    | Q(organising_hub__slug__icontains=hub)
                )
            else:
                queryset = queryset.filter(organising_hub_id=hub_uuid)
        for param, lookup in ((submitted_after, "created_at__date__gte"), (submitted_before, "created_at__date__lte")):
            if param:
                parsed = parse_date(param)
                if not parsed:
                    raise ValidationError({"date": "Submission dates must use YYYY-MM-DD."})
                queryset = queryset.filter(**{lookup: parsed})
        return queryset.order_by("created_at")


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
            review_category=serializer.validated_data.get("review_category", ""),
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
            "review_category": event.review_category,
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

        event = update_event(
            event_id=event.id,
            user=request.user,
            validated_data={"cover_image_url": image_url},
        )

        return Response(
            {
                "success": True,
                "message": "Cover image uploaded successfully.",
                "cover_image_url": image_url,
                "event": HubEventManagementSerializer(event).data,
            },
            status=status.HTTP_200_OK,
        )
