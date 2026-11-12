
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


# ==================================================
# USER MODEL
# ==================================================

class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    email = models.EmailField(
        unique=True,
        db_index=True
    )

    email_verified = models.BooleanField(default=False)

    onboarding_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# ==================================================
# INDIVIDUAL USER PROFILE / VIBESPACE
# ==================================================

class Profile(models.Model):

    class ProfileType(models.TextChoices):
        STUDENT = "student", "Student"
        PROFESSIONAL = "professional", "Professional"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # One profile belongs to exactly one user.
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    # Profile identity
    profile_type = models.CharField(
        max_length=20,
        choices=ProfileType.choices
    )

    byb_signature = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )

    bio = models.CharField(
        max_length=500,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    # Profile images
    profile_picture = models.URLField(
        max_length=500,
        blank=True
    )

    cover_image = models.URLField(
        max_length=500,
        blank=True
    )

    # Student information
    institution = models.CharField(
        max_length=200,
        blank=True
    )

    course = models.CharField(
        max_length=150,
        blank=True
    )

    field_of_study = models.CharField(
        max_length=150,
        blank=True
    )

    academic_year = models.CharField(
        max_length=50,
        blank=True
    )

    graduation_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    # Professional information
    current_organization = models.CharField(
        max_length=200,
        blank=True
    )

    job_title = models.CharField(
        max_length=150,
        blank=True
    )

    industry = models.CharField(
        max_length=150,
        blank=True
    )

    experience_years = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    # Shared interests and skills
    interests = models.JSONField(
        default=list,
        blank=True
    )

    skills = models.JSONField(
        default=list,
        blank=True
    )

    # Social links
    linkedin_url = models.URLField(
        max_length=500,
        blank=True
    )

    github_url = models.URLField(
        max_length=500,
        blank=True
    )

    website_url = models.URLField(
        max_length=500,
        blank=True
    )

    # Privacy
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s VibeSpace"


# ==================================================
# PENDING SIGNUP
# ==================================================

class PendingSignup(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    username = models.CharField(
        max_length=150,
        unique=True
    )

    email = models.EmailField(unique=True)

    password_hash = models.CharField(max_length=128)

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} - {self.email}"


# ==================================================
# EMAIL OTP
# ==================================================

class EmailOTP(models.Model):

    class Purpose(models.TextChoices):
        SIGNUP = "signup", "Signup"
        PASSWORD_RESET = "password_reset", "Password Reset"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    email = models.EmailField(db_index=True)

    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices
    )

    otp_hash = models.CharField(max_length=128)

    attempts = models.PositiveSmallIntegerField(default=0)

    expires_at = models.DateTimeField()

    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.purpose}"
