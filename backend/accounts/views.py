from django.shortcuts import render

# Create your views here.

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import SignupSerializer
from accounts.services.signup_service import start_signup, verify_signup


User = get_user_model()


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
            with transaction.atomic():
                user = verify_signup(
                    email=email,
                    submitted_otp=otp,
                )

                refresh = RefreshToken.for_user(user)

                return Response(
                    {
                        "success": True,
                        "message": "Your BYB account has been created successfully.",
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
                    },
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
