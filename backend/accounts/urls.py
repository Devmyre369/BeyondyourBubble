
from django.urls import path

from accounts.views import SignupView, VerifySignupView


urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path(
        "verify-signup/",
        VerifySignupView.as_view(),
        name="verify-signup",
    ),
]
