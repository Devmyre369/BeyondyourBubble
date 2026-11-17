from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Exists, OuterRef, Value
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Follow, Notification, Profile
from accounts.services.follow_service import (
    follow_user,
    is_following,
    unfollow_user,
)
from accounts.services.notification_service import create_notification
from accounts.social_serializers import PublicConnectionUserSerializer


User = get_user_model()


def get_profile_for_request(request, username):
    profile = get_object_or_404(
        Profile.objects.select_related("user"),
        user__username__iexact=username,
        user__is_active=True,
        user__email_verified=True,
    )
    is_owner = (
        request.user.is_authenticated
        and request.user.pk == profile.user_id
    )
    if profile.visibility != Profile.Visibility.PUBLIC and not is_owner:
        raise Http404
    return profile


def follow_response(follower, followed):
    from django.db.models import Count, Q

    counts = Follow.objects.filter(
        Q(follower=follower) | Q(following=followed)
    ).aggregate(
        target_followers=Count("pk", filter=Q(following=followed)),
        viewer_following=Count("pk", filter=Q(follower=follower)),
    )
    return {
        "target_username": followed.username,
        "is_following": is_following(follower, followed),
        "followers_count": counts["target_followers"],
        "viewer_username": follower.username,
        "viewer_following_count": counts["viewer_following"],
    }


class FollowRelationshipView(APIView):
    def get_permissions(self):
        if self.request.method in ("POST", "DELETE"):
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_target(self, request, username):
        profile = get_profile_for_request(request, username)
        if profile.visibility != Profile.Visibility.PUBLIC:
            raise Http404
        return profile.user

    def get(self, request, username):
        target = self.get_target(request, username)
        return Response({
            "target_username": target.username,
            "is_following": is_following(request.user, target),
            "followers_count": target.follower_relationships.count(),
        })

    def post(self, request, username):
        target = self.get_target(request, username)
        try:
            _, created = follow_user(request.user, target)
        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if created:
            create_notification(
                request.user,
                target,
                Notification.Verb.FOLLOW,
            )

        return Response(
            follow_response(request.user, target),
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )

    def delete(self, request, username):
        target = self.get_target(request, username)
        unfollow_user(request.user, target)
        return Response(
            follow_response(request.user, target),
            status=status.HTTP_200_OK,
        )


class ProfileConnectionsPagination(PageNumberPagination):
    page_size = 20
    page_query_param = "page"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": (
                self.page.next_page_number()
                if self.page.has_next()
                else None
            ),
            "previous": (
                self.page.previous_page_number()
                if self.page.has_previous()
                else None
            ),
            "results": data,
        })


class ProfileConnectionsView(APIView):
    permission_classes = [AllowAny]
    pagination_class = ProfileConnectionsPagination

    def get(self, request, username, relationship):
        profile = get_profile_for_request(request, username)
        if relationship == "followers":
            users = User.objects.filter(
                following_relationships__following=profile.user,
            )
        else:
            users = User.objects.filter(
                follower_relationships__follower=profile.user,
            )

        users = (
            users.filter(
                profile__visibility=Profile.Visibility.PUBLIC,
                is_active=True,
                email_verified=True,
            )
            .select_related("profile")
            .order_by("username", "id")
            .distinct()
        )
        if request.user.is_authenticated:
            users = users.annotate(
                viewer_follows=Exists(
                    Follow.objects.filter(
                        follower_id=request.user.pk,
                        following_id=OuterRef("pk"),
                    )
                )
            )
        else:
            users = users.annotate(
                viewer_follows=Value(
                    False,
                    output_field=BooleanField(),
                )
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users, request, view=self)
        serializer = PublicConnectionUserSerializer(
            page,
            many=True,
        )
        return paginator.get_paginated_response(serializer.data)
