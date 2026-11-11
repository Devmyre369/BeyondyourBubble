
import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from accounts.models import EmailOTP


OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60


def generate_otp():
    """Generate a cryptographically secure six-digit OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


@transaction.atomic
def create_otp(email, purpose):
    email = email.strip().lower()
    now = timezone.now()

    latest_otp = (
        EmailOTP.objects
        .select_for_update()
        .filter(email=email, purpose=purpose)
        .order_by("-created_at")
        .first()
    )

    if latest_otp:
        cooldown_end = (
            latest_otp.created_at
            + timedelta(seconds=OTP_RESEND_COOLDOWN_SECONDS)
        )

        if now < cooldown_end:
            remaining = int(
                (cooldown_end - now).total_seconds()
            ) + 1

            raise ValidationError({
                "otp": (
                    f"Please wait {remaining} seconds "
                    "before requesting another OTP."
                )
            })

    EmailOTP.objects.filter(
        email=email,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)

    otp = generate_otp()

    EmailOTP.objects.create(
        email=email,
        purpose=purpose,
        otp_hash=make_password(otp),
        expires_at=now + timedelta(
            minutes=OTP_EXPIRY_MINUTES
        ),
    )

    return otp


def verify_otp(email, purpose, submitted_otp):
    """
    Verify OTP and persist failed attempts before
    raising validation errors.
    """

    email = email.strip().lower()
    error_message = None

    with transaction.atomic():

        otp_record = (
            EmailOTP.objects
            .select_for_update()
            .filter(
                email=email,
                purpose=purpose,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if not otp_record:
            error_message = (
                "No active OTP found. Please request a new one."
            )

        elif otp_record.expires_at <= timezone.now():
            otp_record.is_used = True
            otp_record.save(update_fields=["is_used"])

            error_message = (
                "OTP has expired. Please request a new one."
            )

        elif otp_record.attempts >= OTP_MAX_ATTEMPTS:
            otp_record.is_used = True
            otp_record.save(update_fields=["is_used"])

            error_message = (
                "Maximum verification attempts reached. "
                "Please request a new OTP."
            )

        elif (
            not isinstance(submitted_otp, str)
            or len(submitted_otp) != 6
            or not submitted_otp.isdigit()
        ):
            otp_record.attempts += 1

            if otp_record.attempts >= OTP_MAX_ATTEMPTS:
                otp_record.is_used = True

            otp_record.save(
                update_fields=["attempts", "is_used"]
            )

            error_message = "Invalid OTP."

        elif not check_password(
            submitted_otp,
            otp_record.otp_hash,
        ):
            otp_record.attempts += 1

            if otp_record.attempts >= OTP_MAX_ATTEMPTS:
                otp_record.is_used = True

            otp_record.save(
                update_fields=["attempts", "is_used"]
            )

            error_message = "Invalid OTP."

        else:
            otp_record.is_used = True
            otp_record.save(update_fields=["is_used"])

    # Raise after the transaction has committed.
    if error_message:
        raise ValidationError({
            "otp": error_message
        })

    return True
