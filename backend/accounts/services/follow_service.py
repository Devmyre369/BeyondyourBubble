from django.db import transaction
from django.db.models import (
    BooleanField,
    Count,
    Exists,
    OuterRef,
    Q,
    Value,
)

from accounts.models import Follow


@transaction.atomic
def follow_user(follower, following):
    if follower.pk == following.pk:
        raise ValueError("You cannot follow yourself.")

    relationship, created = Follow.objects.get_or_create(
        follower=follower,
        following=following,
    )
    return relationship, created


@transaction.atomic
def unfollow_user(follower, following):
    return Follow.objects.filter(
        follower=follower,
        following=following,
    ).delete()[0] > 0


def is_following(follower, following):
    if not follower or not follower.is_authenticated:
        return False

    return Follow.objects.filter(
        follower=follower,
        following=following,
    ).exists()


def annotate_content_follow_state(queryset, viewer, author_field="author_id"):
    if viewer and viewer.is_authenticated:
        return queryset.annotate(
            viewer_follows_author=Exists(
                Follow.objects.filter(
                    follower_id=viewer.pk,
                    following_id=OuterRef(author_field),
                )
            )
        )
    return queryset.annotate(
        viewer_follows_author=Value(
            False,
            output_field=BooleanField(),
        )
    )


def get_profile_statistics(user):
    from vibespace.models import Moment, Vibe

    content_counts = {
        "vibes_count": Vibe.objects.filter(author=user).count(),
        "moments_count": Moment.objects.filter(author=user).count(),
    }
    follow_counts = Follow.objects.filter(
        Q(follower=user) | Q(following=user)
    ).aggregate(
        followers_count=Count(
            "pk",
            filter=Q(following=user),
        ),
        following_count=Count(
            "pk",
            filter=Q(follower=user),
        ),
    )

    return {
        **content_counts,
        "posts_count": content_counts["vibes_count"] + content_counts["moments_count"],
        "followers_count": follow_counts["followers_count"],
        "following_count": follow_counts["following_count"],
    }
