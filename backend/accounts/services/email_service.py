
from django.conf import settings
from django.core.mail import send_mail


def send_signup_otp(email, otp):
    """Send the email verification OTP during signup."""

    subject = "Verify your BYB account"

    message = f"""
Welcome to BYB — Beyond Your Bubble!

Your email verification OTP is:

{otp}

This OTP is valid for 5 minutes.

Do not share this OTP with anyone.

If you did not request this verification, you can ignore this email.

— Team BYB
"""

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def send_password_reset_otp(email, otp):
    """Send the OTP required to reset an account password."""

    subject = "BYB password reset verification"

    message = f"""
We received a request to reset your BYB account password.

Your password reset OTP is:

{otp}

This OTP is valid for 5 minutes.

Do not share this OTP with anyone.

If you did not request a password reset, you can ignore this email.

— Team BYB
"""

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
