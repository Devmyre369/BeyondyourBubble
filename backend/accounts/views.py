
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Profile

from accounts.serializers import (
    SignupSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ProfileSerializer,
)

from accounts.services.signup_service import (
    start_signup,
    verify_signup,
)

from accounts.services.password_reset_service import (
    request_password_reset,
    confirm_password_reset,
)

from accounts.services.profile_image_service import (
    ProfileImageError,
    upload_profile_image,
    delete_profile_image,
)
from accounts.services.profile_image_service import (
    ProfileImageError,
    upload_profile_image,
    delete_profile_image,
)


User = get_user_model()


# ==================================================
# AUTHENTICATION RESPONSE
# ==================================================

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


# ==================================================
# AUTHENTICATION VIEWS
# ==================================================

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


# ==================================================
# MY PROFILE / VIBESPACE
# ==================================================

class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(
            Profile.objects.select_related("user"),
            user=request.user,
        )

        serializer = ProfileSerializer(profile)

        return Response(
            {
                "success": True,
                "profile": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        if Profile.objects.filter(user=request.user).exists():
            return Response(
                {
                    "success": False,
                    "message": "Your profile already exists. Use PATCH to update it.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer = ProfileSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                profile = serializer.save(user=request.user)

                request.user.onboarding_completed = True
                request.user.save(update_fields=["onboarding_completed"])

            return Response(
                {
                    "success": True,
                    "message": "Your BYB profile has been created successfully.",
                    "profile": ProfileSerializer(profile).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": "A profile with conflicting information already exists.",
                },
                status=status.HTTP_409_CONFLICT,
            )

    def patch(self, request):
        profile = get_object_or_404(
            Profile.objects.select_related("user"),
            user=request.user,
        )

        serializer = ProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Your profile has been updated successfully.",
                "profile": serializer.data,
            },
            status=status.HTTP_200_OK,
        )



# ==================================================
# PROFILE IMAGE UPLOAD / DELETE
# ==================================================

class ProfileImageView(APIView):
    permission_classes = [IsAuthenticated]

    ALLOWED_IMAGE_TYPES = {
        "profile_picture",
        "cover_image",
    }

    def post(self, request, image_type):
        if image_type not in self.ALLOWED_IMAGE_TYPES:
            return Response(
                {
                    "success": False,
                    "message": "Invalid image type.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = get_object_or_404(
            Profile.objects.select_related("user"),
            user=request.user,
        )

        uploaded_file = request.FILES.get("image")

        if not uploaded_file:
            return Response(
                {
                    "success": False,
                    "message": "Please select an image to upload.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            image_url = upload_profile_image(
                user_id=request.user.id,
                image_type=image_type,
                uploaded_file=uploaded_file,
            )

            setattr(profile, image_type, image_url)
            profile.save(update_fields=[image_type, "updated_at"])

            return Response(
                {
                    "success": True,
                    "message": "Image uploaded successfully.",
                    "profile": ProfileSerializer(profile).data,
                },
                status=status.HTTP_200_OK,
            )

        except ProfileImageError as error:
            return Response(
                {
                    "success": False,
                    "message": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, image_type):
        if image_type not in self.ALLOWED_IMAGE_TYPES:
            return Response(
                {
                    "success": False,
                    "message": "Invalid image type.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = get_object_or_404(
            Profile.objects.select_related("user"),
            user=request.user,
        )

        if not getattr(profile, image_type):
            return Response(
                {
                    "success": False,
                    "message": "No image is currently set.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            delete_profile_image(
                user_id=request.user.id,
                image_type=image_type,
            )

            setattr(profile, image_type, "")
            profile.save(update_fields=[image_type, "updated_at"])

            return Response(
                {
                    "success": True,
                    "message": "Image removed successfully.",
                    "profile": ProfileSerializer(profile).data,
                },
                status=status.HTTP_200_OK,
            )

        except ProfileImageError as error:
            return Response(
                {
                    "success": False,
                    "message": str(error),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )




# ==================================================
# PUBLIC USER PROFILE
# ==================================================

class PublicProfileView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, username):
        user = get_object_or_404(
            User.objects.filter(
                username__iexact=username,
                is_active=True,
                email_verified=True,
            )
        )

        profile = get_object_or_404(
            Profile.objects.select_related("user"),
            user=user,
            visibility=Profile.Visibility.PUBLIC,
        )

        serializer = ProfileSerializer(profile)

        return Response(
            {
                "success": True,
                "profile": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

# ==================================================
# PROFILE IMAGE UPLOAD / DELETE
# ==================================================

class ProfileImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    ALLOWED_IMAGE_TYPES = {
        "profile_picture",
        "cover_image",
    }

    def post(self, request, image_type):
        if image_type not in self.ALLOWED_IMAGE_TYPES:
            return Response(
                {
                    "success": False,
                    "message": "Invalid image type.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = get_object_or_404(
            Profile.objects.select_related("user"),
            user=request.user,
        )

        uploaded_file = request.FILES.get("image")

        if not uploaded_file:
            return Response(
                {
                    "success": False,
                    "message": "Please select an image to upload.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            image_url = upload_profile_image(
                user_id=request.user.id,
                image_type=image_type,
                uploaded_file=uploaded_file,
            )

            setattr(profile, image_type, image_url)
            profile.save(update_fields=[image_type, "updated_at"])

            return Response(
                {
                    "success": True,
                    "message": "Image uploaded successfully.",
                    "image_type": image_type,
                    "image_url": image_url,
                    "profile": ProfileSerializer(profile).data,
                },
                status=status.HTTP_200_OK,
            )

        except ProfileImageError as error:
            return Response(
                {
                    "success": False,
                    "message": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, image_type):
        if image_type not in self.ALLOWED_IMAGE_TYPES:
            return Response(
                {
                    "success": False,
                    "message": "Invalid image type.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = get_object_or_404(
            Profile.objects.select_related("user"),
            user=request.user,
        )

        current_image = getattr(profile, image_type)

        if not current_image:
            return Response(
                {
                    "success": False,
                    "message": "No image is currently set.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            result = delete_profile_image(
                user_id=request.user.id,
                image_type=image_type,
            )

            if result.get("result") not in {"ok", "not found"}:
                return Response(
                    {
                        "success": False,
                        "message": "Cloudinary could not delete the image.",
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            setattr(profile, image_type, "")
            profile.save(update_fields=[image_type, "updated_at"])

            return Response(
                {
                    "success": True,
                    "message": "Image removed successfully.",
                    "profile": ProfileSerializer(profile).data,
                },
                status=status.HTTP_200_OK,
            )

        except ProfileImageError as error:
            return Response(
                {
                    "success": False,
                    "message": str(error),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
