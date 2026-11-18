
from django.urls import path

from .views import (
    EventChoiceListView,
    EventDiscoveryDetailView,
    EventDiscoveryListCreateView,
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
        "<uuid:id>/",
        EventDiscoveryDetailView.as_view(),
        name="event-discovery-detail",
    ),
]
