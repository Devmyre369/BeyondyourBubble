
from django.urls import path

from .views import (
    EventChoiceListView,
    EventDiscoveryDetailView,
    EventDiscoveryListCreateView,
    EventModerationQueueView,
    EventModerationReviewView,
)


urlpatterns = [
    path(
        "",
        EventDiscoveryListCreateView.as_view(),
        name="event-discovery",
    ),
    path(
        "choices/",
        EventChoiceListView.as_view(),
        name="event-choices",
    ),
    path(
        "moderation/",
        EventModerationQueueView.as_view(),
        name="event-moderation-queue",
    ),
    path(
        "moderation/<uuid:event_id>/review/",
        EventModerationReviewView.as_view(),
        name="event-moderation-review",
    ),
    path(
        "<uuid:id>/",
        EventDiscoveryDetailView.as_view(),
        name="event-discovery-detail",
    ),
]
