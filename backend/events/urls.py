
from django.urls import path

from .views import (
    EventChoiceListView,
    EventCoverImageUploadView,
    EventDiscoveryDetailView,
    EventDiscoveryListCreateView,
    EventModerationQueueView,
    EventModerationReviewView,
    EventRegistrationView,
    HubEventManagementListView,
    EventManagementDetailView,
    EventManagementCancelView,
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
        "<uuid:event_id>/registration/",
        EventRegistrationView.as_view(),
        name="event-registration",
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
        "hubs/<uuid:hub_id>/",
        HubEventManagementListView.as_view(),
        name="hub-event-management",
    ),
    path(
        "manage/<uuid:event_id>/",
        EventManagementDetailView.as_view(),
        name="event-management-detail",
    ),
    path(
        "manage/<uuid:event_id>/cancel/",
        EventManagementCancelView.as_view(),
        name="event-management-cancel",
    ),
    path(
        "manage/<uuid:event_id>/cover-image/",
        EventCoverImageUploadView.as_view(),
        name="event-cover-image-upload",
    ),
    path(
        "<uuid:id>/",
        EventDiscoveryDetailView.as_view(),
        name="event-discovery-detail",
    ),
]
