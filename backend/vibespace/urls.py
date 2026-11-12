
from django.urls import path

from .views import (
    VibeListCreateView,
    VibeDetailView,
    MomentListCreateView,
    MomentDetailView,
)

from .interaction_views import (
    ContentCommentListCreateView,
    CommentDetailView,
    ContentRevibeView,
    SavedContentListCreateView,
    SavedContentDetailView,
)

urlpatterns = [
    # Vibes
    path("vibes/", VibeListCreateView.as_view(), name="vibe-list-create"),
    path("vibes/<uuid:id>/", VibeDetailView.as_view(), name="vibe-detail"),

    # Moments
    path("moments/", MomentListCreateView.as_view(), name="moment-list-create"),
    path("moments/<uuid:id>/", MomentDetailView.as_view(), name="moment-detail"),

    # Comments
    path(
        "<str:content_type>/<uuid:content_id>/comments/",
        ContentCommentListCreateView.as_view(),
        name="content-comment-list-create",
    ),
    path(
        "comments/<uuid:comment_id>/",
        CommentDetailView.as_view(),
        name="comment-detail",
    ),

    # Revibes
    path(
        "<str:content_type>/<uuid:content_id>/revibe/",
        ContentRevibeView.as_view(),
        name="content-revibe",
    ),

    # Saved content
    path("saved/", SavedContentListCreateView.as_view(), name="saved-content-list-create"),
    path(
        "saved/<uuid:saved_id>/",
        SavedContentDetailView.as_view(),
        name="saved-content-detail",
    ),
]
