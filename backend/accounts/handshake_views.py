from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.handshake_serializers import HandshakeItemSerializer
from accounts.models import Handshake, Profile
from accounts.services.handshake_service import (
    cancel_handshake,
    respond_to_handshake,
    send_handshake_request,
)


User = get_user_model()


class HandshakePagination(PageNumberPagination):
    page_size = 20
    page_query_param = "page"
    max_page_size = 100


class HandshakeSendSerializer(serializers.Serializer):
    recipient_username = serializers.CharField(max_length=150, trim_whitespace=True)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({
                    field: ["This field may not be modified."]
                    for field in sorted(unknown)
                })
        return super().to_internal_value(data)


def _public_profile_user(username):
    profile = get_object_or_404(
        Profile.objects.select_related("user"),
        user__username__iexact=username,
        user__is_active=True,
        user__email_verified=True,
        visibility=Profile.Visibility.PUBLIC,
    )
    return profile.user


def _status_for(viewer, target, request):
    low_id, high_id = sorted((viewer.pk, target.pk), key=str)
    handshake = Handshake.objects.filter(
        user_low_id=low_id,
        user_high_id=high_id,
        status__in=[Handshake.Status.PENDING, Handshake.Status.ACCEPTED],
    ).select_related(
        "requester", "requester__profile", "recipient", "recipient__profile",
    ).first()
    if handshake is None:
        state = "none"
    elif handshake.status == Handshake.Status.ACCEPTED:
        state = "connected"
    elif handshake.requester_id == viewer.pk:
        state = "outgoing_pending"
    else:
        state = "incoming_pending"
    return {
        "state": state,
        "request_id": str(handshake.pk) if handshake else None,
        "handshake": (
            HandshakeItemSerializer(handshake, context={"request": request}).data
            if handshake else None
        ),
    }


def _handshake_data(handshake, request):
    handshake = Handshake.objects.select_related(
        "requester", "requester__profile", "recipient", "recipient__profile",
    ).get(pk=handshake.pk)
    return HandshakeItemSerializer(handshake, context={"request": request}).data


class HandshakeStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        target = _public_profile_user(username)
        if target.pk == request.user.pk:
            return Response({"state": "self", "request_id": None, "handshake": None})
        return Response(_status_for(request.user, target, request))


class HandshakeRequestCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = HandshakeSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target = _public_profile_user(serializer.validated_data["recipient_username"])
        handshake, created = send_handshake_request(request.user, target)
        return Response(
            {
                "handshake": _handshake_data(handshake, request),
                "state": _status_for(request.user, target, request),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class HandshakeListView(APIView):
    permission_classes = [IsAuthenticated]
    list_type = "incoming"

    def get_queryset(self, user):
        base = Handshake.objects.select_related(
            "requester", "requester__profile", "recipient", "recipient__profile",
        )
        list_type = self.kwargs.get("list_type", self.list_type)
        if list_type == "incoming":
            return base.filter(recipient=user, status=Handshake.Status.PENDING)
        if list_type == "outgoing":
            return base.filter(requester=user).exclude(status=Handshake.Status.ACCEPTED)
        return base.filter(
            Q(requester=user) | Q(recipient=user),
            status=Handshake.Status.ACCEPTED,
        )

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request.user).order_by("-updated_at", "-created_at")
        paginator = HandshakePagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        data = HandshakeItemSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)


class HandshakeResponseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, handshake_id, decision):
        if decision not in ("accept", "reject", "cancel"):
            return Response({"detail": "Invalid Handshake action."}, status=400)
        if decision == "cancel":
            handshake = cancel_handshake(request.user, handshake_id)
        else:
            handshake = respond_to_handshake(
                request.user,
                handshake_id,
                accept=decision == "accept",
            )
        return Response({"handshake": _handshake_data(handshake, request)})


class HandshakeConnectionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, handshake_id):
        handshake = cancel_handshake(
            request.user,
            handshake_id,
            remove_accepted=True,
        )
        return Response({"handshake": _handshake_data(handshake, request)})
