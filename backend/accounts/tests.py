
from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from PIL import Image

from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
)

from accounts.models import EmailOTP, PendingSignup, Profile

from accounts.services.otp_service import (
    create_otp,
    verify_otp,
)

from accounts.services.signup_service import (
    start_signup,
    verify_signup,
)

from accounts.services.password_reset_service import (
    request_password_reset,
    confirm_password_reset,
)

User = get_user_model()


# ==================================================
# OTP SERVICE TESTS
# ==================================================

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


# ==================================================
# SIGNUP SERVICE TESTS
# ==================================================

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


# ==================================================
# PASSWORD RESET SERVICE TESTS
# ==================================================

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

        with self.assertRaises(TokenError):
            RefreshToken(old_refresh_token)


# ==================================================
# PROFILE API TESTS
# ==================================================

class ProfileAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="profile_test_user",
            email="profile_test@example.com",
            password="Test!Secure_82River",
            email_verified=True,
        )

        self.other_user = User.objects.create_user(
            username="other_profile_user",
            email="other_profile@example.com",
            password="Test!Secure_92Orbit",
            email_verified=True,
        )

        refresh = RefreshToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

        self.profile_url = "/api/accounts/profile/"

    def test_authenticated_user_can_create_profile(self):
        response = self.client.post(
            self.profile_url,
            {
                "first_name": "Devansh",
                "last_name": "Shukla",
                "profile_type": "student",
                "institution": "Test University",
                "course": "Computer Science",
                "city": "Lucknow",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(
            Profile.objects.filter(user=self.user).exists()
        )

        self.user.refresh_from_db()

        self.assertTrue(self.user.onboarding_completed)
        self.assertEqual(self.user.first_name, "Devansh")
        self.assertEqual(self.user.last_name, "Shukla")

        self.assertEqual(
            response.data["profile"]["first_name"],
            "Devansh",
        )

        self.assertEqual(
            response.data["profile"]["last_name"],
            "Shukla",
        )

    def test_user_cannot_create_duplicate_profile(self):
        Profile.objects.create(
            user=self.user,
            profile_type="student",
        )

        response = self.client.post(
            self.profile_url,
            {
                "profile_type": "student",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 409)

        self.assertEqual(
            Profile.objects.filter(user=self.user).count(),
            1,
        )

    def test_authenticated_user_can_retrieve_own_profile(self):
        Profile.objects.create(
            user=self.user,
            profile_type="student",
            institution="Test University",
        )

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["profile"]["username"],
            self.user.username,
        )

        self.assertEqual(
            response.data["profile"]["first_name"],
            "",
        )

        self.assertEqual(
            response.data["profile"]["last_name"],
            "",
        )

    def test_authenticated_user_can_update_own_profile(self):
        Profile.objects.create(
            user=self.user,
            profile_type="student",
        )

        response = self.client.patch(
            self.profile_url,
            {
                "bio": "Connecting beyond boundaries.",
                "city": "Lucknow",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        profile = Profile.objects.get(user=self.user)

        self.assertEqual(
            profile.bio,
            "Connecting beyond boundaries.",
        )

        self.assertEqual(profile.city, "Lucknow")

    def test_user_can_update_first_and_last_name(self):
        Profile.objects.create(
            user=self.user,
            profile_type="student",
        )

        response = self.client.patch(
            self.profile_url,
            {
                "first_name": "Updated",
                "last_name": "Name",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")

        self.assertEqual(
            response.data["profile"]["first_name"],
            "Updated",
        )

        self.assertEqual(
            response.data["profile"]["last_name"],
            "Name",
        )

    def test_public_profile_is_visible_to_other_users(self):
        Profile.objects.create(
            user=self.other_user,
            profile_type="professional",
            visibility="public",
        )

        response = self.client.get(
            f"{self.profile_url}{self.other_user.username}/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["profile"]["username"],
            self.other_user.username,
        )

    def test_private_profile_is_not_visible_to_other_users(self):
        Profile.objects.create(
            user=self.other_user,
            profile_type="professional",
            visibility="private",
        )

        response = self.client.get(
            f"{self.profile_url}{self.other_user.username}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_cannot_access_own_profile(self):
        self.client.credentials()

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_user_cannot_create_profile(self):
        self.client.credentials()

        response = self.client.post(
            self.profile_url,
            {
                "profile_type": "student",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)


# ==================================================
# PROFILE IMAGE API TESTS
# ==================================================

class ProfileImageAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="image_test_user",
            email="image_test@example.com",
            password="Test!Secure_82River",
            email_verified=True,
        )

        Profile.objects.create(
            user=self.user,
            profile_type="student",
        )

        refresh = RefreshToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

        self.profile_picture_url = (
            "/api/accounts/profile/image/profile_picture/"
        )

        self.cover_image_url = (
            "/api/accounts/profile/image/cover_image/"
        )

    @staticmethod
    def create_test_image(name="test.png", image_format="PNG"):
        image_buffer = BytesIO()

        image = Image.new("RGB", (10, 10), color="red")
        image.save(image_buffer, format=image_format)

        return SimpleUploadedFile(
            name=name,
            content=image_buffer.getvalue(),
            content_type=f"image/{image_format.lower()}",
        )

    @patch("accounts.views.upload_profile_image")
    def test_user_can_upload_profile_picture(self, mock_upload):
        mock_upload.return_value = (
            "https://res.cloudinary.com/test/profile_picture.jpg"
        )

        image = self.create_test_image()

        response = self.client.post(
            self.profile_picture_url,
            {"image": image},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

        profile = Profile.objects.get(user=self.user)

        self.assertEqual(
            profile.profile_picture,
            mock_upload.return_value,
        )

        mock_upload.assert_called_once()

    @patch("accounts.views.upload_profile_image")
    def test_user_can_upload_cover_image(self, mock_upload):
        mock_upload.return_value = (
            "https://res.cloudinary.com/test/cover_image.jpg"
        )

        image = self.create_test_image()

        response = self.client.post(
            self.cover_image_url,
            {"image": image},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

        profile = Profile.objects.get(user=self.user)

        self.assertEqual(
            profile.cover_image,
            mock_upload.return_value,
        )

        mock_upload.assert_called_once()

    @patch("accounts.services.profile_image_service.uploader.upload")
    def test_invalid_image_file_is_rejected(self, mock_upload):
        image = SimpleUploadedFile(
            "invalid.png",
            b"This is not a valid image.",
            content_type="image/png",
        )

        response = self.client.post(
            self.profile_picture_url,
            {"image": image},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        mock_upload.assert_not_called()

    @patch("accounts.services.profile_image_service.uploader.upload")
    def test_oversized_profile_picture_is_rejected(self, mock_upload):
        image = SimpleUploadedFile(
            "large.png",
            b"x" * (5 * 1024 * 1024 + 1),
            content_type="image/png",
        )

        response = self.client.post(
            self.profile_picture_url,
            {"image": image},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        mock_upload.assert_not_called()

    @patch("accounts.services.profile_image_service.uploader.upload")
    def test_oversized_cover_image_is_rejected(self, mock_upload):
        image = SimpleUploadedFile(
            "large.png",
            b"x" * (10 * 1024 * 1024 + 1),
            content_type="image/png",
        )

        response = self.client.post(
            self.cover_image_url,
            {"image": image},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        mock_upload.assert_not_called()

    @patch("accounts.views.delete_profile_image")
    def test_user_can_delete_profile_picture(self, mock_delete):
        mock_delete.return_value = {"result": "ok"}

        profile = Profile.objects.get(user=self.user)

        profile.profile_picture = (
            "https://res.cloudinary.com/test/profile_picture.jpg"
        )
        profile.save()

        response = self.client.delete(
            self.profile_picture_url
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

        profile.refresh_from_db()

        self.assertEqual(profile.profile_picture, "")

        mock_delete.assert_called_once()

    @patch("accounts.views.delete_profile_image")
    def test_user_can_delete_cover_image(self, mock_delete):
        mock_delete.return_value = {"result": "ok"}

        profile = Profile.objects.get(user=self.user)

        profile.cover_image = (
            "https://res.cloudinary.com/test/cover_image.jpg"
        )
        profile.save()

        response = self.client.delete(
            self.cover_image_url
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

        profile.refresh_from_db()

        self.assertEqual(profile.cover_image, "")

        mock_delete.assert_called_once()

    @patch("accounts.views.delete_profile_image")
    def test_deleting_missing_image_returns_404(self, mock_delete):
        response = self.client.delete(
            self.profile_picture_url
        )

        self.assertEqual(response.status_code, 404)
        mock_delete.assert_not_called()

    @patch("accounts.views.upload_profile_image")
    def test_unauthenticated_user_cannot_upload_image(self, mock_upload):
        self.client.credentials()

        image = self.create_test_image()

        response = self.client.post(
            self.profile_picture_url,
            {"image": image},
            format="multipart",
        )

        self.assertEqual(response.status_code, 401)
        mock_upload.assert_not_called()

    @patch("accounts.views.upload_profile_image")
    def test_upload_requires_an_image(self, mock_upload):
        response = self.client.post(
            self.profile_picture_url,
            {},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        mock_upload.assert_not_called()
