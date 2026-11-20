
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
from events.models import Event

from .feed_serializers import FeedEntrySerializer
from .models import Vibe, Moment, SavedContent


class FeedPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"


def build_feed_entries(vibes, moments, events=()):
    combined = []

    for vibe in vibes:
        profile = getattr(vibe.author, "profile", None)
        visible_event = _visible_event(vibe.event)
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
            "event_id": visible_event.id if visible_event else None,
            "event_title": visible_event.title if visible_event else None,
            "event_hub_id": None,
            "event_hub_name": None,
            "event_cover_image_url": "",
            "event_starts_at": None,
            "event_venue": "",
            "event_city": "",
            "event_category": "",
            "event_format": "",
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
        visible_event = _visible_event(moment.event)
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
            "event_id": visible_event.id if visible_event else None,
            "event_title": visible_event.title if visible_event else None,
            "event_hub_id": None,
            "event_hub_name": None,
            "event_cover_image_url": "",
            "event_starts_at": None,
            "event_venue": "",
            "event_city": "",
            "event_category": "",
            "event_format": "",
            "content_text": moment.caption or "",
            "image_url": moment.image_url,
            "created_at": moment.created_at,
            "like_count": moment.like_count,
            "comment_count": moment.comment_count,
            "revibe_count": moment.revibe_count,
            "save_count": moment.save_count,
            "share_count": moment.share_count,
        })

    for event in events:
        profile = getattr(event.created_by, "profile", None)
        public_profile = bool(
            profile
            and profile.visibility == Profile.Visibility.PUBLIC
            and event.created_by.is_active
            and event.created_by.email_verified
        )
        venue = "Online event" if event.format == Event.Format.ONLINE else event.venue_name
        combined.append({
            "id": event.id,
            "content_type": "event",
            "author_username": event.created_by.username,
            "author_first_name": event.created_by.first_name if public_profile else "",
            "author_last_name": event.created_by.last_name if public_profile else "",
            "author_profile_picture": (
                profile.profile_picture
                if public_profile and profile.profile_picture
                else ""
            ),
            "author_byb_signature": profile.byb_signature if public_profile else None,
            "is_following": getattr(event, "viewer_follows_author", False),
            "event_id": event.id,
            "event_title": event.title,
            "event_hub_id": event.organising_hub_id,
            "event_hub_name": event.organising_hub.name,
            "event_cover_image_url": event.cover_image_url,
            "event_starts_at": event.starts_at,
            "event_venue": venue,
            "event_city": event.city,
            "event_category": event.category,
            "event_format": event.format,
            "content_text": event.description,
            "image_url": "",
            "created_at": event.created_at,
            "like_count": 0,
            "comment_count": 0,
            "revibe_count": 0,
            "save_count": 0,
            "share_count": 0,
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


def _visible_event(event):
    if (
        event
        and event.status == Event.Status.PUBLISHED
        and event.moderation_status == Event.ModerationStatus.APPROVED
        and event.organising_hub.is_active
    ):
        return event
    return None


class FeedView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = FeedPagination

    def get(self, request):
        user = request.user

        # Public-profile content plus the authenticated user's own content.
        visibility_filter = Q(author=user) | Q(
            author__profile__visibility=Profile.Visibility.PUBLIC,
            author__is_active=True,
            author__email_verified=True,
        )

        vibes = annotate_content_follow_state(
            Vibe.objects
            .filter(visibility_filter)
            .select_related("author", "author__profile", "event__organising_hub"),
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
            .select_related("author", "author__profile", "event__organising_hub"),
            user,
        ).annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
            revibe_count=Count("revibes", distinct=True),
            save_count=Count("saved_by", distinct=True),
            share_count=Count("shares", distinct=True),
        ).order_by("-created_at", "-id")

        events = annotate_content_follow_state(
            Event.objects.filter(
                status=Event.Status.PUBLISHED,
                moderation_status=Event.ModerationStatus.APPROVED,
                organising_hub__is_active=True,
            ).select_related(
                "created_by", "created_by__profile", "organising_hub",
            ),
            user,
            author_field="created_by_id",
        ).order_by("-created_at", "-id")

        # Calculate total feed entries.
        total_count = vibes.count() + moments.count() + events.count()

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
        combined = build_feed_entries(
            list(vibes[:end]),
            list(moments[:end]),
            list(events[:end]),
        )
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

        visibility_filter = Q(
            author=profile.user,
            author__is_active=True,
            author__email_verified=True,
        )
        vibes = annotate_content_follow_state(
            Vibe.objects
            .filter(visibility_filter)
            .select_related("author", "author__profile", "event__organising_hub"),
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
            .select_related("author", "author__profile", "event__organising_hub"),
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

        content_visible = Q(
            author__profile__visibility=Profile.Visibility.PUBLIC,
            author__is_active=True,
            author__email_verified=True,
        ) | Q(author=user)
        saved = SavedContent.objects.filter(user=user).filter(
            Q(vibe__isnull=False) & (
                Q(vibe__author__profile__visibility=Profile.Visibility.PUBLIC,
                  vibe__author__is_active=True, vibe__author__email_verified=True)
                | Q(vibe__author=user)
            )
            | Q(moment__isnull=False) & (
                Q(moment__author__profile__visibility=Profile.Visibility.PUBLIC,
                  moment__author__is_active=True, moment__author__email_verified=True)
                | Q(moment__author=user)
            )
        ).order_by("-created_at", "-id")
        total_count = saved.count()

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

        saved_rows = list(saved.values_list("vibe_id", "moment_id")[start:end])
        page_order = [
            ("vibe", str(vibe_id)) if vibe_id else ("moment", str(moment_id))
            for vibe_id, moment_id in saved_rows
        ]
        vibe_ids = [item_id for kind, item_id in page_order if kind == "vibe"]
        moment_ids = [item_id for kind, item_id in page_order if kind == "moment"]

        vibes = annotate_content_follow_state(
            Vibe.objects
            .filter(content_visible, id__in=vibe_ids)
            .select_related("author", "author__profile", "event__organising_hub"),
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
            .filter(content_visible, id__in=moment_ids)
            .select_related("author", "author__profile", "event__organising_hub"),
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

