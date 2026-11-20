from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Hub, HubMembership
from .permissions import CanEditHub, can_edit_hub
from .serializers import (
    HubCreateSerializer,
    HubDetailSerializer,
    HubDiscoveryQuerySerializer,
    HubListSerializer,
    HubInviteSerializer,
    HubMemberRoleSerializer,
    HubMemberSerializer,
    HubMembershipStateSerializer,
    StrictMembershipInputSerializer,
    HubUpdateSerializer,
)
from .services.membership_service import (
    can_manage_hub_members,
    change_member_role,
    get_active_hub,
    invite_member,
    join_hub,
    leave_hub,
    remove_member,
    review_membership_request,
)
from .services.hub_image_service import HubImageError, upload_hub_image


class HubPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"

    def paginate_queryset(self, queryset, request, view=None):
        page_number = request.query_params.get(self.page_query_param, "1")

        try:
            page_number = int(page_number)
            if page_number < 1:
                raise ValueError
        except (TypeError, ValueError):
            raise NotFound("Invalid page number.")

        self.page_number = page_number
        self.count = queryset.count()
        start = (page_number - 1) * self.page_size
        self.end = start + self.page_size

        return list(queryset[start:self.end])

    def get_paginated_response(self, data):
        return Response({
            "count": self.count,
            "next": self.page_number + 1 if self.end < self.count else None,
            "previous": self.page_number - 1 if self.page_number > 1 else None,
            "results": data,
        })


class HubDiscoveryView(generics.ListCreateAPIView):
    serializer_class = HubListSerializer
    pagination_class = HubPagination
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return HubCreateSerializer
        return HubListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hub = serializer.save()
        response_data = HubDetailSerializer(
            hub,
            context=self.get_serializer_context(),
        ).data
        headers = self.get_success_headers(response_data)
        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def get_queryset(self):
        query_serializer = HubDiscoveryQuerySerializer(
            data=self.request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data

        queryset = Hub.objects.filter(is_active=True)

        if filters.get("hub_type"):
            queryset = queryset.filter(hub_type=filters["hub_type"])

        if filters.get("city"):
            queryset = queryset.filter(city__iexact=filters["city"])

        if filters.get("search"):
            search = filters["search"]
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(short_description__icontains=search)
                | Q(description__icontains=search)
                | Q(slug__icontains=search)
                | Q(college_or_parent_organisation__icontains=search)
            )

        return queryset.order_by("-created_at", "-id")


class HubDetailView(generics.RetrieveUpdateAPIView):
    queryset = Hub.objects.filter(is_active=True)
    serializer_class = HubDetailSerializer
    permission_classes = [IsAuthenticated, CanEditHub]
    http_method_names = ["get", "patch", "head", "options"]
    lookup_field = "id"
    lookup_url_kwarg = "hub_id"

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return HubUpdateSerializer
        return HubDetailSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        hub = self.get_object()
        response.data = HubDetailSerializer(
            hub,
            context=self.get_serializer_context(),
        ).data
        return response


def _membership_state(hub, user, membership):
    can_manage = can_manage_hub_members(user, hub)
    can_leave = bool(
        membership
        and membership.status == HubMembership.Status.APPROVED
        and membership.user_id != hub.owner_id
        and membership.role
        in (
            HubMembership.Role.ADMIN,
            HubMembership.Role.EDITOR,
            HubMembership.Role.MEMBER,
        )
    )
    return {
        "membership": (
            HubMembershipStateSerializer(membership).data
            if membership
            else None
        ),
        "membership_policy": hub.membership_policy,
        "can_leave": can_leave,
        "can_manage_members": can_manage,
        "pending_request_count": (
            hub.memberships.filter(status=HubMembership.Status.PENDING).count()
            if can_manage
            else None
        ),
    }


class HubMembershipView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, hub_id):
        hub = get_active_hub(hub_id)
        membership = HubMembership.objects.filter(
            hub=hub,
            user=request.user,
        ).first()
        return Response(_membership_state(hub, request.user, membership))

    def post(self, request, hub_id):
        serializer = StrictMembershipInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hub, membership = join_hub(hub_id, request.user)
        return Response(
            _membership_state(hub, request.user, membership),
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, hub_id):
        serializer = StrictMembershipInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        leave_hub(hub_id, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class HubMembersView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = HubPagination

    def get(self, request, hub_id):
        hub = get_active_hub(hub_id)
        members = (
            HubMembership.objects.filter(
                hub=hub,
                status=HubMembership.Status.APPROVED,
            )
            .select_related("user", "user__profile")
            .order_by("created_at", "id")
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(members, request, view=self)
        data = HubMemberSerializer(page, many=True).data
        return paginator.get_paginated_response(data)


class HubPendingRequestsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = HubPagination

    def get(self, request, hub_id):
        hub = get_active_hub(hub_id)
        if not can_manage_hub_members(request.user, hub):
            raise PermissionDenied(
                "Only the Hub owner or an approved administrator can view requests."
            )

        requests = (
            HubMembership.objects.filter(
                hub=hub,
                status=HubMembership.Status.PENDING,
            )
            .select_related("user", "user__profile")
            .order_by("created_at", "id")
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(requests, request, view=self)
        data = HubMemberSerializer(page, many=True).data
        return paginator.get_paginated_response(data)


class HubMembershipRequestReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, hub_id, membership_id, decision):
        serializer = StrictMembershipInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = review_membership_request(
            hub_id,
            membership_id,
            request.user,
            decision,
        )
        membership = (
            HubMembership.objects.select_related("user", "user__profile")
            .get(pk=membership.pk)
        )
        return Response(HubMemberSerializer(membership).data)


class HubMemberInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, hub_id):
        serializer = HubInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership, created = invite_member(
            hub_id,
            request.user,
            serializer.validated_data["username"],
        )
        membership = (
            HubMembership.objects.select_related("user", "user__profile")
            .get(pk=membership.pk)
        )
        return Response(
            HubMemberSerializer(membership).data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class HubMemberRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, hub_id, membership_id):
        serializer = StrictMembershipInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        remove_member(hub_id, membership_id, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class HubMemberRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, hub_id, membership_id):
        serializer = HubMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = change_member_role(
            hub_id,
            membership_id,
            request.user,
            serializer.validated_data["role"],
        )
        membership = (
            HubMembership.objects.select_related("user", "user__profile")
            .get(pk=membership.pk)
        )
        return Response(HubMemberSerializer(membership).data)


class HubImageUploadView(APIView):
    """
    Upload a Hub logo or cover image directly to Cloudinary.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    allowed_image_types = {"logo", "cover_image"}

    def post(self, request, hub_id, image_type):
        hub = (
            Hub.objects
            .filter(id=hub_id, is_active=True)
            .first()
        )

        if hub is None:
            raise NotFound("Hub not found.")

        if not can_edit_hub(request.user, hub):
            raise PermissionDenied(
                "You do not have permission to edit this Hub."
            )

        if image_type not in self.allowed_image_types:
            raise NotFound("Image type not found.")

        uploaded_file = request.FILES.get("image")

        if not uploaded_file:
            return Response(
                {"message": "Please select an image to upload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            image_url = upload_hub_image(
                hub_id=hub.id,
                image_type=image_type,
                uploaded_file=uploaded_file,
            )
        except HubImageError as exc:
            return Response(
                {"message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        setattr(hub, image_type, image_url)
        hub.save(update_fields=[image_type])

        response_data = HubDetailSerializer(
            hub,
            context={"request": request},
        ).data

        return Response(response_data, status=status.HTTP_200_OK)
