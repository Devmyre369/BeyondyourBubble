
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Profile, UserSettings

from accounts.serializers import (
    SignupSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ProfileSerializer,
    UserSettingsSerializer,

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
from accounts.services.follow_service import (
    get_profile_statistics,
    is_following,
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
            "is_staff": user.is_staff,
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
                "statistics": get_profile_statistics(request.user),
                "is_following": False,
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
# PUBLIC USER PROFILE
# ==================================================

class PublicProfileView(APIView):
    permission_classes = [AllowAny]

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
        )
        is_owner = (
            request.user.is_authenticated
            and request.user.pk == user.pk
        )
        if (
            profile.visibility != Profile.Visibility.PUBLIC
            and not is_owner
        ):
            raise Http404

        serializer = ProfileSerializer(profile)

        return Response(
            {
                "success": True,
                "profile": serializer.data,
                "statistics": get_profile_statistics(user),
                "is_following": is_following(request.user, user),
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
\n\n# ==================================================\n# USER SETTINGS VIEWS\n# ==================================================\n\nclass UserSettingsView(APIView):\n    permission_classes = [IsAuthenticated]\n\n    def get(self, request):\n        settings_obj, _ = UserSettings.objects.get_or_create(\n            user=request.user\n        )\n        serializer = UserSettingsSerializer(settings_obj)\n        return Response(\n            {\n                "success": True,\n                "settings": serializer.data,\n            },\n            status=status.HTTP_200_OK,\n        )\n\n    def patch(self, request):\n        settings_obj, _ = UserSettings.objects.get_or_create(\n            user=request.user\n        )\n        serializer = UserSettingsSerializer(\n            settings_obj,\n            data=request.data,\n            partial=True,\n        )\n        serializer.is_valid(raise_exception=True)\n        serializer.save()\n        return Response(\n            {\n                "success": True,\n                "settings": serializer.data,\n            },\n            status=status.HTTP_200_OK,\n        )\n\n\nclass ChangePasswordView(APIView):\n    permission_classes = [IsAuthenticated]\n\n    def post(self, request):\n        current_password = request.data.get(\"current_password\", \"\")\n        new_password = request.data.get(\"new_password\", \"\")\n        confirm_password = request.data.get(\"confirm_password\", \"\")\n\n        if not request.user.check_password(current_password):\n            return Response(\n                {\n                    "success": False,\n                    "message": "Current password is incorrect.",\n                },\n                status=status.HTTP_400_BAD_REQUEST,\n            )\n\n        if new_password != confirm_password:\n            return Response(\n                {\n                    "success": False,\n                    "message": "New passwords do not match.",\n                },\n                status=status.HTTP_400_BAD_REQUEST,\n            )\n\n        from django.contrib.auth.password_validation import validate_password\n        from django.core.exceptions import ValidationError as DjangoValidationError\n\n        try:\n            validate_password(new_password, user=request.user)\n        except DjangoValidationError as error:\n            return Response(\n                {\n                    "success": False,\n                    "message": list(error.messages),\n                },\n                status=status.HTTP_400_BAD_REQUEST,\n            )\n\n        request.user.set_password(new_password)\n        request.user.save(update_fields=[\"password\"])\n\n        return Response(\n            {\n                "success": True,\n                "message": "Password changed successfully.",\n            },\n            status=status.HTTP_200_OK,\n        )\n\n\nclass DeleteAccountView(APIView):\n    permission_classes = [IsAuthenticated]\n\n    def post(self, request):\n        password = request.data.get(\"password\", \"\")\n        confirmation = request.data.get(\"confirmation\", \"\")\n\n        if confirmation != \"DELETE\":\n            return Response(\n                {\n                    "success": False,\n                    "message": "Type DELETE to confirm account deletion.",\n                },\n                status=status.HTTP_400_BAD_REQUEST,\n            )\n\n        if not request.user.check_password(password):\n            return Response(\n                {\n                    "success": False,\n                    "message": "Password is incorrect.",\n                },\n                status=status.HTTP_400_BAD_REQUEST,\n            )\n\n        # Block deletion if the user owns hubs/events to avoid\n        # cascading destruction of shared resources.\n        from hubs.models import Hub\n        from events.models import Event\n\n        if Hub.objects.filter(owner=request.user).exists():\n            return Response(\n                {\n                    "success": False,\n                    "message": (\n                        "You own one or more Hubs. Transfer or delete "\n                        "them before deleting your account."\n                    ),\n                },\n                status=status.HTTP_409_CONFLICT,\n            )\n\n        if Event.objects.filter(created_by=request.user).exists():\n            return Response(\n                {\n                    "success": False,\n                    "message": (\n                        "You have created events. Remove them before "\n                        "deleting your account."\n                    ),\n                },\n                status=status.HTTP_409_CONFLICT,\n            )\n\n        user = request.user\n        user.delete()\n\n        return Response(\n            {\n                "success": True,\n                "message": "Account deleted.",\n            },\n            status=status.HTTP_200_OK,\n        )\n
            )
