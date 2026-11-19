
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Profile
from accounts.services.follow_service import annotate_content_follow_state

from .feed_serializers import FeedEntrySerializer
from .models import Vibe, Moment, SavedContent


class FeedPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"


def build_feed_entries(vibes, moments):
    combined = []

    for vibe in vibes:
        profile = getattr(vibe.author, "profile", None)
        combined.append({
            "id": vibe.id,
            "content_type": "vibe",
            "author_username": vibe.author.username,
            "author_first_name": vibe.author.first_name,
            "author_last_name": vibe.author.last_name,
            "author_profile_picture": (
                profile.profile_picture if profile and profile.profile_picture else ""
            ),
            "author_byb_signature": profile.byb_signature if profile else None,
            "is_following": getattr(vibe, "viewer_follows_author", False),
            "event_id": vibe.event_id,
            "event_title": vibe.event.title if vibe.event else None,
            "content_text": vibe.text,
            "image_url": "",
            "created_at": vibe.created_at,
            "like_count": vibe.like_count,
            "comment_count": vibe.comment_count,
            "revibe_count": vibe.revibe_count,
            "save_count": vibe.save_count,
            "share_count": vibe.share_count,
        })

    for moment in moments:
        profile = getattr(moment.author, "profile", None)
        combined.append({
            "id": moment.id,
            "content_type": "moment",
            "author_username": moment.author.username,
            "author_first_name": moment.author.first_name,
            "author_last_name": moment.author.last_name,
            "author_profile_picture": (
                profile.profile_picture if profile and profile.profile_picture else ""
            ),
            "author_byb_signature": profile.byb_signature if profile else None,
            "is_following": getattr(moment, "viewer_follows_author", False),
            "event_id": moment.event_id,
            "event_title": moment.event.title if moment.event else None,
            "content_text": moment.caption or "",
            "image_url": moment.image_url,
            "created_at": moment.created_at,
            "like_count": moment.like_count,
            "comment_count": moment.comment_count,
            "revibe_count": moment.revibe_count,
            "save_count": moment.save_count,
            "share_count": moment.share_count,
        })

    combined.sort(
        key=lambda item: (
            item["created_at"],
            str(item["id"]),
            item["content_type"],
        ),
        reverse=True,
    )
    return combined


class FeedView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = FeedPagination

    def get(self, request):
        user = request.user

        # Public-profile content plus the authenticated user's own content.
        visibility_filter = (
            Q(author__profile__visibility=Profile.Visibility.PUBLIC)
            | Q(author=user)
        )

        vibes = annotate_content_follow_state(
            Vibe.objects
            .filter(visibility_filter)
            .select_related("author", "author__profile", "event"),
            user,
        ).annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
            revibe_count=Count("revibes", distinct=True),
            save_count=Count("saved_by", distinct=True),
            share_count=Count("shares", distinct=True),
        ).order_by("-created_at", "-id")

        moments = annotate_content_follow_state(
            Moment.objects
            .filter(visibility_filter)
            .select_related("author", "author__profile", "event"),
            user,
        ).annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
            revibe_count=Count("revibes", distinct=True),
            save_count=Count("saved_by", distinct=True),
            share_count=Count("shares", distinct=True),
        ).order_by("-created_at", "-id")

        # Calculate total feed entries.
        total_count = vibes.count() + moments.count()

        paginator = self.pagination_class()
        page_number = request.query_params.get("page", "1")

        try:
            page_number = int(page_number)
            if page_number < 1:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"detail": "Invalid page number."},
                status=status.HTTP_404_NOT_FOUND,
            )

        start = (page_number - 1) * paginator.page_size
        end = start + paginator.page_size

        # Fetch only enough entries from each content type
        # to construct the requested combined page.
        vibes = list(vibes[:end])
        moments = list(moments[:end])
        combined = build_feed_entries(vibes, moments)
        page_items = combined[start:end]

        serializer = FeedEntrySerializer(page_items, many=True)

        return Response({
            "count": total_count,
            "next": page_number + 1 if end < total_count else None,
            "previous": page_number - 1 if page_number > 1 else None,
            "results": serializer.data,
        })


class ProfilePostsView(APIView):
    permission_classes = [AllowAny]
    pagination_class = FeedPagination

    def get(self, request, username):
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
        if (
            profile.visibility != Profile.Visibility.PUBLIC
            and not is_owner
        ):
            raise Http404

        visibility_filter = Q(author=profile.user)
        vibes = annotate_content_follow_state(
            Vibe.objects
            .filter(visibility_filter)
            .select_related("author", "author__profile", "event"),
            request.user,
        ).annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
            revibe_count=Count("revibes", distinct=True),
            save_count=Count("saved_by", distinct=True),
            share_count=Count("shares", distinct=True),
        ).order_by("-created_at", "-id")
        moments = annotate_content_follow_state(
            Moment.objects
            .filter(visibility_filter)
            .select_related("author", "author__profile", "event"),
            request.user,
        ).annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
            revibe_count=Count("revibes", distinct=True),
            save_count=Count("saved_by", distinct=True),
            share_count=Count("shares", distinct=True),
        ).order_by("-created_at", "-id")

        total_count = vibes.count() + moments.count()
        paginator = self.pagination_class()
        try:
            page_number = int(request.query_params.get("page", "1"))
            if page_number < 1:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"detail": "Invalid page number."},
                status=status.HTTP_404_NOT_FOUND,
            )

        start = (page_number - 1) * paginator.page_size
        end = start + paginator.page_size
        if start >= total_count and page_number > 1:
            return Response(
                {"detail": "Invalid page."},
                status=status.HTTP_404_NOT_FOUND,
            )

        combined = build_feed_entries(
            list(vibes[:end]),
            list(moments[:end]),
        )
        serializer = FeedEntrySerializer(
            combined[start:end],
            many=True,
        )
        return Response({
            "count": total_count,
            "next": page_number + 1 if end < total_count else None,
            "previous": page_number - 1 if page_number > 1 else None,
            "results": serializer.data,
        })


class SavedFeedView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = FeedPagination

    def get(self, request):
        user = request.user

        saved_rows = list(
            SavedContent.objects
            .filter(user=user)
            .order_by("-created_at")
            .values_list("vibe_id", "moment_id")
        )

        order = []
        for vibe_id, moment_id in saved_rows:
            if vibe_id:
                order.append(("vibe", str(vibe_id)))
            elif moment_id:
                order.append(("moment", str(moment_id)))

        total_count = len(order)

        paginator = self.pagination_class()
        try:
            page_number = int(request.query_params.get("page", "1"))
            if page_number < 1:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"detail": "Invalid page number."},
                status=status.HTTP_404_NOT_FOUND,
            )

        start = (page_number - 1) * paginator.page_size
        end = start + paginator.page_size
        if start >= total_count and page_number > 1:
            return Response(
                {"detail": "Invalid page."},
                status=status.HTTP_404_NOT_FOUND,
            )

        page_order = order[start:end]
        vibe_ids = [item_id for kind, item_id in page_order if kind == "vibe"]
        moment_ids = [item_id for kind, item_id in page_order if kind == "moment"]

        visibility_filter = (
            Q(author__profile__visibility=Profile.Visibility.PUBLIC)
            | Q(author=user)
        )

        vibes = annotate_content_follow_state(
            Vibe.objects
            .filter(visibility_filter, id__in=vibe_ids)
            .select_related("author", "author__profile", "event"),
            user,
        ).annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
            revibe_count=Count("revibes", distinct=True),
            save_count=Count("saved_by", distinct=True),
            share_count=Count("shares", distinct=True),
        )

        moments = annotate_content_follow_state(
            Moment.objects
            .filter(visibility_filter, id__in=moment_ids)
            .select_related("author", "author__profile", "event"),
            user,
        ).annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
            revibe_count=Count("revibes", distinct=True),
            save_count=Count("saved_by", distinct=True),
            share_count=Count("shares", distinct=True),
        )

        entries = build_feed_entries(list(vibes), list(moments))
        entries_map = {
            (entry["content_type"], str(entry["id"])): entry
            for entry in entries
        }
        page_entries = [
            entries_map[key] for key in page_order if key in entries_map
        ]

        serializer = FeedEntrySerializer(page_entries, many=True)
        return Response({
            "count": total_count,
            "next": page_number + 1 if end < total_count else None,
            "previous": page_number - 1 if page_number > 1 else None,
            "results": serializer.data,
        })

