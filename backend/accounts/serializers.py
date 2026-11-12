
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from accounts.models import Profile


User = get_user_model()


# ==================================================
# AUTHENTICATION SERIALIZERS
# ==================================================

class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        min_length=3,
        trim_whitespace=True
    )

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False
    )

    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False
    )

    def validate_username(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Username cannot be empty."
            )

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "This username is already taken."
            )

        return value

    def validate_email(self, value):
        value = value.strip().lower()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate(self, attrs):
        password = attrs["password"]
        confirm_password = attrs["confirm_password"]

        if password != confirm_password:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        try:
            validate_password(password)
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                "password": list(error.messages)
            })

        return attrs


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        trim_whitespace=True
    )

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False
    )

    def validate(self, attrs):
        username = attrs["username"].strip()
        password = attrs["password"]

        request = self.context.get("request")

        user = authenticate(
            request=request,
            username=username,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        if not user.is_active or not user.email_verified:
            raise serializers.ValidationError(
                "This account is not eligible to log in."
            )

        attrs["user"] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()

    otp = serializers.RegexField(
        regex=r"^\d{6}$",
        error_messages={
            "invalid": "Enter a valid six-digit OTP."
        }
    )

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False
    )

    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False
    )

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        try:
            validate_password(attrs["new_password"])
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                "new_password": list(error.messages)
            })

        return attrs


# ==================================================
# PROFILE / VIBESPACE SERIALIZER
# ==================================================

class ProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = Profile

        fields = [
            "id",
            "username",
            "profile_type",
            "byb_signature",
            "bio",
            "city",
            "profile_picture",
            "cover_image",

            # Student information
            "institution",
            "course",
            "field_of_study",
            "academic_year",
            "graduation_year",

            # Professional information
            "current_organization",
            "job_title",
            "industry",
            "experience_years",

            # Shared information
            "interests",
            "skills",

            # Social links
            "linkedin_url",
            "github_url",
            "website_url",

            # Privacy
            "visibility",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "created_at",
            "updated_at",
        ]

    def validate_bio(self, value):
        return value.strip()

    def validate_byb_signature(self, value):
        if not value:
            return value

        value = value.strip()

        queryset = Profile.objects.filter(
            byb_signature__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "This BYB signature is already taken."
            )

        return value

    def validate_interests(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Interests must be a list."
            )

        if len(value) > 30:
            raise serializers.ValidationError(
                "You can add a maximum of 30 interests."
            )

        if not all(
            isinstance(item, str) and item.strip()
            for item in value
        ):
            raise serializers.ValidationError(
                "Every interest must be a non-empty string."
            )

        return list(dict.fromkeys(
            item.strip() for item in value
        ))

    def validate_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Skills must be a list."
            )

        if len(value) > 30:
            raise serializers.ValidationError(
                "You can add a maximum of 30 skills."
            )

        if not all(
            isinstance(item, str) and item.strip()
            for item in value
        ):
            raise serializers.ValidationError(
                "Every skill must be a non-empty string."
            )

        return list(dict.fromkeys(
            item.strip() for item in value
        ))

    def validate_graduation_year(self, value):
        if value is not None and not 2000 <= value <= 2100:
            raise serializers.ValidationError(
                "Enter a valid graduation year."
            )

        return value

    def validate_experience_years(self, value):
        if value is not None and value > 60:
            raise serializers.ValidationError(
                "Experience years cannot exceed 60."
            )

        return value
