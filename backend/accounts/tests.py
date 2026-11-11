
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from accounts.models import EmailOTP, PendingSignup
from accounts.services.otp_service import (
    create_otp,
    verify_otp,
)
from accounts.services.signup_service import (
    start_signup,
    verify_signup,
)
from django.contrib.auth.hashers import check_password

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
)

from accounts.services.password_reset_service import (
    request_password_reset,
    confirm_password_reset,
)

User = get_user_model()


class OTPServiceTests(TestCase):

    def setUp(self):
        self.email = "otptest@example.com"
        self.purpose = EmailOTP.Purpose.SIGNUP

    def test_five_incorrect_attempts_invalidate_otp(self):
        create_otp(self.email, self.purpose)

        for _ in range(5):
            with self.assertRaises(ValidationError):
                verify_otp(self.email, self.purpose, "000000")

        otp_record = EmailOTP.objects.get(
            email=self.email,
            purpose=self.purpose,
        )

        self.assertEqual(otp_record.attempts, 5)
        self.assertTrue(otp_record.is_used)

    def test_sixth_attempt_does_not_increase_counter(self):
        create_otp(self.email, self.purpose)

        for _ in range(5):
            with self.assertRaises(ValidationError):
                verify_otp(self.email, self.purpose, "000000")

        with self.assertRaises(ValidationError):
            verify_otp(self.email, self.purpose, "000000")

        otp_record = EmailOTP.objects.get(
            email=self.email,
            purpose=self.purpose,
        )

        self.assertEqual(otp_record.attempts, 5)
        self.assertTrue(otp_record.is_used)

    def test_expired_otp_is_invalidated(self):
        create_otp(self.email, self.purpose)

        otp_record = EmailOTP.objects.get(
            email=self.email,
            purpose=self.purpose,
        )

        otp_record.expires_at = (
            timezone.now() - timedelta(minutes=1)
        )
        otp_record.save(update_fields=["expires_at"])

        with self.assertRaises(ValidationError):
            verify_otp(self.email, self.purpose, "123456")

        otp_record.refresh_from_db()

        self.assertEqual(otp_record.attempts, 0)
        self.assertTrue(otp_record.is_used)

    def test_correct_otp_can_only_be_used_once(self):
        otp = create_otp(self.email, self.purpose)

        self.assertTrue(
            verify_otp(self.email, self.purpose, otp)
        )

        with self.assertRaises(ValidationError):
            verify_otp(self.email, self.purpose, otp)

        otp_record = EmailOTP.objects.get(
            email=self.email,
            purpose=self.purpose,
        )

        self.assertTrue(otp_record.is_used)

    def test_resend_cooldown_blocks_new_otp(self):
        create_otp(self.email, self.purpose)

        with self.assertRaises(ValidationError):
            create_otp(self.email, self.purpose)

        self.assertEqual(
            EmailOTP.objects.filter(
                email=self.email,
                purpose=self.purpose,
            ).count(),
            1,
        )


class SignupServiceTests(TestCase):

    def setUp(self):
        self.username = "signup_test_user"
        self.email = "signup_test@example.com"
        self.password = "Test!Secure_82River"

    @patch("accounts.services.signup_service.send_signup_otp")
    def test_start_signup_creates_pending_signup(self, mock_email):
        mock_email.return_value = 1

        result = start_signup(
            username=self.username,
            email=self.email,
            password=self.password,
        )

        self.assertEqual(result["email"], self.email)
        self.assertTrue(
            PendingSignup.objects.filter(
                email=self.email
            ).exists()
        )
        self.assertFalse(
            User.objects.filter(email=self.email).exists()
        )
        mock_email.assert_called_once()

    @patch("accounts.services.signup_service.send_signup_otp")
    def test_verify_signup_creates_verified_user(self, mock_email):
        mock_email.return_value = 1

        start_signup(
            username=self.username,
            email=self.email,
            password=self.password,
        )

        otp_record = EmailOTP.objects.get(
            email=self.email,
            purpose=EmailOTP.Purpose.SIGNUP,
        )

        from django.contrib.auth.hashers import check_password

        # Retrieve the OTP from the mocked email call.
        otp = mock_email.call_args.args[1]

        user = verify_signup(
            email=self.email,
            submitted_otp=otp,
        )

        self.assertEqual(user.username, self.username)
        self.assertTrue(user.email_verified)
        self.assertTrue(
            check_password(self.password, user.password)
        )
        self.assertFalse(
            PendingSignup.objects.filter(
                email=self.email
            ).exists()
        )
        self.assertTrue(otp_record.pk)

    @patch("accounts.services.signup_service.send_signup_otp")
    def test_incorrect_signup_otp_does_not_create_user(self, mock_email):
        mock_email.return_value = 1

        start_signup(
            username=self.username,
            email=self.email,
            password=self.password,
        )

        with self.assertRaises(ValidationError):
            verify_signup(
                email=self.email,
                submitted_otp="000000",
            )

        self.assertFalse(
            User.objects.filter(email=self.email).exists()
        )

        otp_record = EmailOTP.objects.get(
            email=self.email,
            purpose=EmailOTP.Purpose.SIGNUP,
        )

        self.assertEqual(otp_record.attempts, 1)
        self.assertFalse(otp_record.is_used)

class PasswordResetServiceTests(TestCase):

    def setUp(self):
        self.username = "reset_test_user"
        self.email = "reset_test@example.com"
        self.old_password = "Old!Secure_82River"
        self.new_password = "New!Secure_92Orbit"

        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.old_password,
            email_verified=True,
        )

    @patch(
        "accounts.services.password_reset_service.send_password_reset_otp"
    )
    def test_password_reset_request_creates_otp(self, mock_email):
        mock_email.return_value = 1

        request_password_reset(self.email)

        self.assertTrue(
            EmailOTP.objects.filter(
                email=self.email,
                purpose=EmailOTP.Purpose.PASSWORD_RESET,
                is_used=False,
            ).exists()
        )

        mock_email.assert_called_once()

    @patch(
        "accounts.services.password_reset_service.send_password_reset_otp"
    )
    def test_incorrect_reset_otp_increments_attempts(self, mock_email):
        mock_email.return_value = 1

        request_password_reset(self.email)

        with self.assertRaises(ValidationError):
            confirm_password_reset(
                email=self.email,
                otp="000000",
                new_password=self.new_password,
            )

        otp_record = EmailOTP.objects.get(
            email=self.email,
            purpose=EmailOTP.Purpose.PASSWORD_RESET,
        )

        self.assertEqual(otp_record.attempts, 1)
        self.assertFalse(otp_record.is_used)

        self.user.refresh_from_db()

        self.assertTrue(
            check_password(self.old_password, self.user.password)
        )

    @patch(
        "accounts.services.password_reset_service.send_password_reset_otp"
    )
    def test_successful_reset_changes_password_and_blacklists_refresh_token(
        self,
        mock_email,
    ):
        mock_email.return_value = 1

        request_password_reset(self.email)

        otp = mock_email.call_args.args[1]

        # Create an outstanding refresh token before resetting.
        refresh = RefreshToken.for_user(self.user)
        old_refresh_token = str(refresh)

        result = confirm_password_reset(
            email=self.email,
            otp=otp,
            new_password=self.new_password,
        )

        self.assertTrue(result)

        self.user.refresh_from_db()

        self.assertTrue(
            check_password(self.new_password, self.user.password)
        )

        self.assertFalse(
            check_password(self.old_password, self.user.password)
        )

        self.assertTrue(
            BlacklistedToken.objects.filter(
                token__user=self.user
            ).exists()
        )

        # The old refresh token must no longer be accepted.
        with self.assertRaises(TokenError):
            RefreshToken(old_refresh_token)
