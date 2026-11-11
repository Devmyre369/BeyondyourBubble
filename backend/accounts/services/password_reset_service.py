
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction

from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from accounts.models import EmailOTP
from accounts.services.otp_service import create_otp, verify_otp
from accounts.services.email_service import send_password_reset_otp


User = get_user_model()


@transaction.atomic
def request_password_reset(email):
    email = email.strip().lower()

    user = User.objects.filter(
        email__iexact=email,
        is_active=True,
        email_verified=True,
    ).first()

    if not user:
        return

    otp = create_otp(
        email=user.email,
        purpose=EmailOTP.Purpose.PASSWORD_RESET,
    )

    result = send_password_reset_otp(user.email, otp)

    if result != 1:
        raise ValidationError(
            "Unable to send the password reset email. Please try again."
        )


def confirm_password_reset(email, otp, new_password):
    email = email.strip().lower()

    user = User.objects.filter(
        email__iexact=email,
        is_active=True,
        email_verified=True,
    ).first()

    if not user:
        raise ValidationError({
            "email": "Unable to complete password reset."
        })

    # Verify OTP separately so failed attempts are committed.
    verify_otp(
        email=user.email,
        purpose=EmailOTP.Purpose.PASSWORD_RESET,
        submitted_otp=otp,
    )

    # Update password and revoke existing refresh tokens atomically.
    with transaction.atomic():

        user = (
            User.objects
            .select_for_update()
            .get(pk=user.pk)
        )

        user.password = make_password(new_password)
        user.save(update_fields=["password"])

        outstanding_tokens = OutstandingToken.objects.filter(
            user=user
        )

        BlacklistedToken.objects.bulk_create(
            [
                BlacklistedToken(token=token)
                for token in outstanding_tokens
            ],
            ignore_conflicts=True,
        )

    return True
