
from django.urls import path

from accounts.views import (
    SignupView,
    VerifySignupView,
    LoginView,
)


urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path(
        "verify-signup/",
        VerifySignupView.as_view(),
        name="verify-signup",
    ),
    path("login/", LoginView.as_view(), name="login"),
]
