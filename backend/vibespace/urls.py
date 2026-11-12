
from django.urls import path

from .views import (
    VibeListCreateView,
    VibeDetailView,
    MomentListCreateView,
    MomentDetailView,
)


urlpatterns = [
    # Vibes
    path(
        "vibes/",
        VibeListCreateView.as_view(),
        name="vibe-list-create",
    ),
    path(
        "vibes/<uuid:id>/",
        VibeDetailView.as_view(),
        name="vibe-detail",
    ),

    # Moments
    path(
        "moments/",
        MomentListCreateView.as_view(),
        name="moment-list-create",
    ),
    path(
        "moments/<uuid:id>/",
        MomentDetailView.as_view(),
        name="moment-detail",
    ),
]
