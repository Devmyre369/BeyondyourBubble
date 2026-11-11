from django.db import models

# Create your models here.

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom BYB user model.
    Users can log in using their username and password.
    """

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

    def __str__(self):
        return self.username


class EmailOTP(models.Model):
    """
    Stores email OTP verification records.
    OTPs will be stored as hashes, not plaintext.
    """

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
