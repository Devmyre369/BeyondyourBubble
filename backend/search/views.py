from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Profile
from events.models import Event
from hubs.models import Hub
from vibespace.models import Moment, Vibe


User = get_user_model()


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(
        min_length=2,
        max_length=120,
        trim_whitespace=True,
    )
    category = serializers.ChoiceField(
        choices=["all", "posts", "users", "events", "hubs"],
        required=False,
        default="all",
    )
    page = serializers.IntegerField(
        required=False,
        min_value=1,
        default=1,
    )
    page_size = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=20,
        default=10,
    )


class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query_serializer = SearchQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data
        query = params["q"]
        category = params["category"]
        page = params["page"]
        page_size = params["page_size"]
        offset = (page - 1) * page_size
        end = offset + page_size

        visible_content = (
            Q(author__profile__visibility=Profile.Visibility.PUBLIC)
            | Q(author=request.user)
        )
        vibes = (
            Vibe.objects.filter(visible_content)
            .filter(
                Q(text__icontains=query)
                | Q(author__username__icontains=query)
                | Q(event__title__icontains=query)
            )
            .select_related("author", "author__profile", "event")
            .order_by("-created_at", "-id")
        )
        moments = (
            Moment.objects.filter(visible_content)
            .filter(
                Q(caption__icontains=query)
                | Q(author__username__icontains=query)
                | Q(event__title__icontains=query)
            )
            .select_related("author", "author__profile", "event")
            .order_by("-created_at", "-id")
        )

        users = (
            User.objects.filter(
                Q(profile__visibility=Profile.Visibility.PUBLIC)
                | Q(pk=request.user.pk)
            )
            .filter(
                is_active=True,
                email_verified=True,
                profile__isnull=False,
            )
            .filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(profile__bio__icontains=query)
                | Q(profile__city__icontains=query)
                | Q(profile__institution__icontains=query)
                | Q(profile__current_organization__icontains=query)
                | Q(profile__job_title__icontains=query)
            )
            .select_related("profile")
            .order_by("username", "id")
            .distinct()
        )
        events = (
            Event.objects.filter(
                status__in=[
                    Event.Status.PUBLISHED,
                    Event.Status.COMPLETED,
                ]
            )
            .filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(venue_name__icontains=query)
                | Q(city__icontains=query)
            )
            .order_by("-starts_at", "-created_at", "-id")
        )
        hubs = (
            Hub.objects.filter(is_active=True)
            .filter(
                Q(name__icontains=query)
                | Q(short_description__icontains=query)
                | Q(description__icontains=query)
                | Q(slug__icontains=query)
                | Q(city__icontains=query)
                | Q(college_or_parent_organisation__icontains=query)
            )
            .order_by("-created_at", "-id")
        )

        post_count = vibes.count() + moments.count()
        counts = {
            "posts": post_count,
            "users": users.count(),
            "events": events.count(),
            "hubs": hubs.count(),
        }
        results = {
            "posts": [],
            "users": [],
            "events": [],
            "hubs": [],
        }
        has_more = {
            name: offset + page_size < count
            for name, count in counts.items()
        }

        if category in ("all", "posts"):
            post_entries = []
            for vibe in vibes[:end]:
                profile = getattr(vibe.author, "profile", None)
                post_entries.append({
                    "id": str(vibe.id),
                    "content_type": "vibe",
                    "author_username": vibe.author.username,
                    "author_profile_picture": (
                        profile.profile_picture
                        if profile and profile.profile_picture
                        else ""
                    ),
                    "content_text": vibe.text,
                    "image_url": "",
                    "event_title": vibe.event.title if vibe.event else None,
                    "created_at": vibe.created_at,
                })
            for moment in moments[:end]:
                profile = getattr(moment.author, "profile", None)
                post_entries.append({
                    "id": str(moment.id),
                    "content_type": "moment",
                    "author_username": moment.author.username,
                    "author_profile_picture": (
                        profile.profile_picture
                        if profile and profile.profile_picture
                        else ""
                    ),
                    "content_text": moment.caption,
                    "image_url": moment.image_url,
                    "event_title": moment.event.title if moment.event else None,
                    "created_at": moment.created_at,
                })
            post_entries.sort(
                key=lambda item: (item["created_at"], item["id"]),
                reverse=True,
            )
            results["posts"] = post_entries[offset:end]

        if category in ("all", "users"):
            results["users"] = [
                {
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "profile_type": user.profile.profile_type,
                    "profile_picture": user.profile.profile_picture,
                    "bio": user.profile.bio,
                    "city": user.profile.city,
                }
                for user in users[offset:end]
            ]

        if category in ("all", "events"):
            results["events"] = [
                {
                    "id": str(event.id),
                    "title": event.title,
                    "description": event.description,
                    "starts_at": event.starts_at,
                    "venue_name": event.venue_name,
                    "city": event.city,
                }
                for event in events[offset:end]
            ]

        if category in ("all", "hubs"):
            results["hubs"] = [
                {
                    "id": str(hub.id),
                    "name": hub.name,
                    "slug": hub.slug,
                    "hub_type": hub.hub_type,
                    "short_description": hub.short_description,
                    "logo": hub.logo,
                    "city": hub.city,
                    "is_verified": hub.is_verified,
                }
                for hub in hubs[offset:end]
            ]

        return Response({
            "query": query,
            "category": category,
            "page": page,
            "page_size": page_size,
            "counts": counts,
            "has_more": has_more,
            "results": results,
        })
