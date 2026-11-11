
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    SignupView,
    VerifySignupView,
    LoginView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)


urlpatterns = [
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
]
