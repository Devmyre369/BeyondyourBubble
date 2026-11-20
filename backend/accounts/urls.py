
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    ProfileImageView,
    SignupView,
    VerifySignupView,
    LoginView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    MyProfileView,
    PublicProfileView,
)
from accounts.social_views import (
    FollowRelationshipView,
    ProfileConnectionsView,
)
from accounts.notification_views import (
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
    NotificationUnreadCountView,
)
from accounts.handshake_views import (
    HandshakeConnectionDetailView,
    HandshakeListView,
    HandshakeRequestCreateView,
    HandshakeResponseView,
    HandshakeStatusView,
)


urlpatterns = [
    # Authentication
    path("signup/", SignupView.as_view(), name="signup"),

    path(
        "verify-signup/",
        VerifySignupView.as_view(),
        name="verify-signup",
    ),

    path("login/", LoginView.as_view(), name="login"),

    path(
        "password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset",
    ),

    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),

    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),

    # Individual profile / VibeSpace
    path(
        "profile/",
        MyProfileView.as_view(),
        name="my-profile",
    ),

    path(
        "profile/<str:username>/follow/",
        FollowRelationshipView.as_view(),
        name="profile-follow",
    ),

    path(
        "profile/<str:username>/followers/",
        ProfileConnectionsView.as_view(),
        {"relationship": "followers"},
        name="profile-followers",
    ),

    path(
        "profile/<str:username>/following/",
        ProfileConnectionsView.as_view(),
        {"relationship": "following"},
        name="profile-following",
    ),
    path("handshakes/", HandshakeRequestCreateView.as_view(), name="handshake-request-create"),
    path("handshakes/status/<str:username>/", HandshakeStatusView.as_view(), name="handshake-status"),
    path("handshakes/incoming/", HandshakeListView.as_view(), {"list_type": "incoming"}, name="handshake-incoming"),
    path("handshakes/outgoing/", HandshakeListView.as_view(), {"list_type": "outgoing"}, name="handshake-outgoing"),
    path("handshakes/connections/", HandshakeListView.as_view(), {"list_type": "connections"}, name="handshake-connections"),
    path("handshakes/requests/<uuid:handshake_id>/<str:decision>/", HandshakeResponseView.as_view(), name="handshake-request-action"),
    path("handshakes/connections/<uuid:handshake_id>/", HandshakeConnectionDetailView.as_view(), name="handshake-connection-detail"),
    path(
        "notifications/",
        NotificationListView.as_view(),
        name="notification-list",
    ),
    path(
        "notifications/read-all/",
        NotificationReadAllView.as_view(),
        name="notification-read-all",
    ),
    path(
        "notifications/unread-count/",
        NotificationUnreadCountView.as_view(),
        name="notification-unread-count",
    ),
    path(
        "notifications/<uuid:notification_id>/read/",
        NotificationReadView.as_view(),
        name="notification-read",
    ),

    path(
        "profile/<str:username>/",
        PublicProfileView.as_view(),
        name="public-profile",
    ),

    path(
        "profile/image/<str:image_type>/",
        ProfileImageView.as_view(),
        name="profile-image",
    ),
]
