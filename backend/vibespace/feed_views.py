
from django.db.models import Q
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .feed_serializers import FeedEntrySerializer
from accounts.models import Profile

from .models import Vibe, Moment
from .serializers import VibeSerializer, MomentSerializer


class FeedPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"


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

        vibes = (
            Vibe.objects
            .filter(visibility_filter)
            .select_related("author", "author__profile", "event")
            .order_by("-created_at", "-id")
        )

        moments = (
            Moment.objects
            .filter(visibility_filter)
            .select_related("author", "author__profile", "event")
            .order_by("-created_at", "-id")
        )

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

        combined = []

        for vibe in vibes:
            profile = getattr(vibe.author, "profile", None)

            combined.append({
                "id": vibe.id,
                "content_type": "vibe",
                "author_username": vibe.author.username,
                "author_profile_picture": (
                    profile.profile_picture if profile and profile.profile_picture else ""
                ),
                "event_id": vibe.event_id,
                "event_title": vibe.event.title if vibe.event else None,
                "content_text": vibe.text,
                "image_url": "",
                "created_at": vibe.created_at,
            })

        for moment in moments:
            profile = getattr(moment.author, "profile", None)

            combined.append({
                "id": moment.id,
                "content_type": "moment",
                "author_username": moment.author.username,
                "author_profile_picture": (
                    profile.profile_picture if profile and profile.profile_picture else ""
                ),
                "event_id": moment.event_id,
                "event_title": moment.event.title if moment.event else None,
                "content_text": moment.caption or "",
                "image_url": moment.image_url,
                "created_at": moment.created_at,
            })

        # Merge both content types into one newest-first timeline.
        combined.sort(
            key=lambda item: (
                item["created_at"],
                str(item["id"]),
                item["content_type"],
            ),
            reverse=True,
        )

        page_items = combined[start:end]

        serializer = FeedEntrySerializer(page_items, many=True)

        return Response({
            "count": total_count,
            "next": page_number + 1 if end < total_count else None,
            "previous": page_number - 1 if page_number > 1 else None,
            "results": serializer.data,
        })
