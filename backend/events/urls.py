from django.urls import path

from .views import EventChoiceListView


urlpatterns = [
    path(
        "choices/",
        EventChoiceListView.as_view(),
        name="event-choices",
    ),
]