
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from accounts.models import EmailOTP, PendingSignup
from accounts.services.otp_service import create_otp, verify_otp
from accounts.services.email_service import send_signup_otp


User = get_user_model()

PENDING_SIGNUP_EXPIRY_MINUTES = 15


@transaction.atomic
def start_signup(username, email, password):
    username = username.strip()
    email = email.strip().lower()

    if User.objects.filter(username__iexact=username).exists():
        raise ValidationError({
            "username": "This username is already taken."
        })

    if User.objects.filter(email__iexact=email).exists():
        raise ValidationError({
            "email": "An account with this email already exists."
        })

    now = timezone.now()

    PendingSignup.objects.filter(
        expires_at__lte=now
    ).delete()

    existing_pending = PendingSignup.objects.filter(
        Q(username__iexact=username)
        | Q(email__iexact=email)
    )

    for pending in existing_pending:
        same_signup = (
            pending.username.lower() == username.lower()
            and pending.email.lower() == email.lower()
        )

        if not same_signup:
            raise ValidationError(
                "This username or email is already being used "
                "for another pending signup."
            )

    existing_pending.delete()

    PendingSignup.objects.create(
        username=username,
        email=email,
        password_hash=make_password(password),
        expires_at=now + timedelta(
            minutes=PENDING_SIGNUP_EXPIRY_MINUTES
        ),
    )

    otp = create_otp(
        email=email,
        purpose=EmailOTP.Purpose.SIGNUP,
    )

    email_result = send_signup_otp(email, otp)

    if email_result != 1:
        raise ValidationError(
            "Unable to send the verification email. Please try again."
        )

    return {
        "message": "Verification OTP sent successfully.",
        "email": email,
    }


def verify_signup(email, submitted_otp):
    email = email.strip().lower()

    pending_signup = PendingSignup.objects.filter(
        email__iexact=email
    ).first()

    if not pending_signup:
        raise ValidationError({
            "email": "No pending signup found. Please sign up again."
        })

    if pending_signup.expires_at <= timezone.now():
        raise ValidationError({
            "signup": "Your signup session has expired. Please sign up again."
        })

    # OTP verification commits its own transaction.
    verify_otp(
        email=email,
        purpose=EmailOTP.Purpose.SIGNUP,
        submitted_otp=submitted_otp,
    )

    # Only successful account creation happens here.
    with transaction.atomic():

        pending_signup = (
            PendingSignup.objects
            .select_for_update()
            .filter(email__iexact=email)
            .first()
        )

        if not pending_signup:
            raise ValidationError({
                "email": "No pending signup found. Please sign up again."
            })

        if pending_signup.expires_at <= timezone.now():
            raise ValidationError({
                "signup": "Your signup session has expired. Please sign up again."
            })

        if User.objects.filter(
            Q(username__iexact=pending_signup.username)
            | Q(email__iexact=email)
        ).exists():
            raise ValidationError(
                "An account with this username or email already exists."
            )

        user = User(
            username=pending_signup.username,
            email=pending_signup.email,
            email_verified=True,
        )

        user.password = pending_signup.password_hash
        user.save()

        pending_signup.delete()

    return user
