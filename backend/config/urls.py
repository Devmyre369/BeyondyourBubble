from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/vibespace/", include("vibespace.urls")),
    path("api/events/", include("events.urls")),
    path("api/hubs/", include("hubs.urls")),
    path("api/search/", include("search.urls")),
]
