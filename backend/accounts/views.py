
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import (
    SignupSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

from accounts.services.signup_service import (
    start_signup,
    verify_signup,
)

from accounts.services.password_reset_service import (
    request_password_reset,
    confirm_password_reset,
)


User = get_user_model()


def generate_auth_response(user, message):
    refresh = RefreshToken.for_user(user)

    return {
        "success": True,
        "message": message,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "email_verified": user.email_verified,
        },
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
    }


class SignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = start_signup(
                username=serializer.validated_data["username"],
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )

            return Response(
                {
                    "success": True,
                    "message": result["message"],
                    "email": result["email"],
                },
                status=status.HTTP_200_OK,
            )

        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": "This username or email is already in use.",
                },
                status=status.HTTP_409_CONFLICT,
            )


class VerifySignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        otp = request.data.get("otp", "")

        if not email or not otp:
            return Response(
                {
                    "success": False,
                    "message": "Email and OTP are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(otp, str):
            return Response(
                {
                    "success": False,
                    "message": "OTP must be a six-digit string.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = verify_signup(
                email=email,
                submitted_otp=otp,
            )

            return Response(
                generate_auth_response(
                    user,
                    "Your BYB account has been created successfully.",
                ),
                status=status.HTTP_201_CREATED,
            )

        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": "An account with this username or email already exists.",
                },
                status=status.HTTP_409_CONFLICT,
            )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        return Response(
            generate_auth_response(user, "Login successful."),
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        request_password_reset(
            email=serializer.validated_data["email"]
        )

        return Response(
            {
                "success": True,
                "message": (
                    "If an eligible account exists for this email, "
                    "a password reset OTP will be sent."
                ),
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        confirm_password_reset(
            email=data["email"],
            otp=data["otp"],
            new_password=data["new_password"],
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Password reset successful. "
                    "Please log in with your new password."
                ),
            },
            status=status.HTTP_200_OK,
        )
