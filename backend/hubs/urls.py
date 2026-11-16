from django.urls import path

from .views import HubDetailView, HubDiscoveryView


urlpatterns = [
    path("", HubDiscoveryView.as_view(), name="hub-list"),
    path("<uuid:hub_id>/", HubDetailView.as_view(), name="hub-detail"),
]
