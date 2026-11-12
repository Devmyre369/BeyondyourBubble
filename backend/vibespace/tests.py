from django.test import TestCase

# Create your tests here.

from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User, Profile
from events.models import Event
from .models import Vibe, Moment


class VibeSpaceAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.owner = self.create_user("owner")
        self.other_user = self.create_user("other")
        self.private_user = self.create_user("private")

        self.owner_profile = self.create_profile(
            self.owner,
            Profile.Visibility.PUBLIC,
        )

        self.other_profile = self.create_profile(
            self.other_user,
            Profile.Visibility.PUBLIC,
        )

        self.private_profile = self.create_profile(
            self.private_user,
            Profile.Visibility.PRIVATE,
        )

    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPassword123!",
            email_verified=True,
        )

    def create_profile(self, user, visibility):
        return Profile.objects.create(
            user=user,
            profile_type=Profile.ProfileType.STUDENT,
            visibility=visibility,
        )

    def create_event(self, organiser):
        return Event.objects.create(
            organiser=organiser,
            title="BYB Test Event",
            description="Test event",
            city="Lucknow",
            status=Event.Status.PUBLISHED,
        )

    def create_test_image(self):
        image_buffer = BytesIO()

        image = Image.new("RGB", (10, 10), "red")
        image.save(image_buffer, format="PNG")

        return SimpleUploadedFile(
            "moment.png",
            image_buffer.getvalue(),
            content_type="image/png",
        )

    # ==================================================
    # VIBE TESTS
    # ==================================================

    def test_authenticated_user_can_create_vibe(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            "/api/vibespace/vibes/",
            {"text": "My first BYB Vibe"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(Vibe.objects.count(), 1)

        vibe = Vibe.objects.first()

        self.assertEqual(vibe.author, self.owner)
        self.assertEqual(vibe.text, "My first BYB Vibe")
        self.assertIsNone(vibe.event)

    def test_unauthenticated_user_cannot_create_vibe(self):
        response = self.client.post(
            "/api/vibespace/vibes/",
            {"text": "Unauthorized Vibe"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertEqual(Vibe.objects.count(), 0)

    def test_user_can_associate_vibe_with_own_event(self):
        event = self.create_event(self.owner)

        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            "/api/vibespace/vibes/",
            {
                "text": "My event experience",
                "event": str(event.id),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Vibe.objects.first().event,
            event,
        )

    def test_user_cannot_associate_vibe_with_another_users_event(self):
        event = self.create_event(self.other_user)

        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            "/api/vibespace/vibes/",
            {
                "text": "Trying to associate another event",
                "event": str(event.id),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(Vibe.objects.count(), 0)

    def test_author_can_update_vibe(self):
        vibe = Vibe.objects.create(
            author=self.owner,
            text="Original Vibe",
        )

        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            f"/api/vibespace/vibes/{vibe.id}/",
            {"text": "Updated Vibe"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        vibe.refresh_from_db()

        self.assertEqual(vibe.text, "Updated Vibe")

    def test_other_user_cannot_update_vibe(self):
        vibe = Vibe.objects.create(
            author=self.owner,
            text="Original Vibe",
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            f"/api/vibespace/vibes/{vibe.id}/",
            {"text": "Unauthorized update"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        vibe.refresh_from_db()

        self.assertEqual(vibe.text, "Original Vibe")

    def test_author_can_delete_vibe(self):
        vibe = Vibe.objects.create(
            author=self.owner,
            text="Vibe to delete",
        )

        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(
            f"/api/vibespace/vibes/{vibe.id}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Vibe.objects.filter(id=vibe.id).exists()
        )

    # ==================================================
    # PROFILE PRIVACY TESTS
    # ==================================================

    def test_anonymous_user_cannot_see_private_profile_vibes(self):
        Vibe.objects.create(
            author=self.private_user,
            text="Private Vibe",
        )

        response = self.client.get(
            "/api/vibespace/vibes/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(len(response.data), 0)

    def test_private_user_can_see_own_vibes(self):
        vibe = Vibe.objects.create(
            author=self.private_user,
            text="My private Vibe",
        )

        self.client.force_authenticate(
            user=self.private_user
        )

        response = self.client.get(
            "/api/vibespace/vibes/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            str(response.data[0]["id"]),
            str(vibe.id),
        )

    def test_public_vibes_are_visible_to_anonymous_users(self):
        vibe = Vibe.objects.create(
            author=self.owner,
            text="Public Vibe",
        )

        response = self.client.get(
            "/api/vibespace/vibes/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            str(response.data[0]["id"]),
            str(vibe.id),
        )

    # ==================================================
    # MOMENT TESTS
    # ==================================================

    @patch("vibespace.views.upload_moment_image")
    def test_authenticated_user_can_create_moment(
        self,
        mock_upload,
    ):
        mock_upload.return_value = {
            "image_url": "https://example.com/moment.png",
            "cloudinary_public_id": "byb/test/moment",
        }

        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            "/api/vibespace/moments/",
            {
                "caption": "My first BYB Moment",
                "image": self.create_test_image(),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(Moment.objects.count(), 1)

        moment = Moment.objects.first()

        self.assertEqual(moment.author, self.owner)
        self.assertEqual(
            moment.caption,
            "My first BYB Moment",
        )

        self.assertEqual(
            moment.image_url,
            "https://example.com/moment.png",
        )

        mock_upload.assert_called_once()

    def test_moment_creation_requires_authentication(self):
        response = self.client.post(
            "/api/vibespace/moments/",
            {
                "caption": "Unauthorized Moment",
                "image": self.create_test_image(),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertEqual(Moment.objects.count(), 0)

    @patch("vibespace.views.delete_moment_image")
    def test_author_can_delete_moment(self, mock_delete):
        moment = Moment.objects.create(
            author=self.owner,
            image_url="https://example.com/moment.png",
            cloudinary_public_id="byb/test/moment",
            caption="Moment to delete",
        )

        mock_delete.return_value = {"result": "ok"}

        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(
            f"/api/vibespace/moments/{moment.id}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            Moment.objects.filter(id=moment.id).exists()
        )

        mock_delete.assert_called_once_with(
            "byb/test/moment"
        )

    @patch("vibespace.views.delete_moment_image")
    def test_other_user_cannot_delete_moment(self, mock_delete):
        moment = Moment.objects.create(
            author=self.owner,
            image_url="https://example.com/moment.png",
            cloudinary_public_id="byb/test/moment",
        )

        self.client.force_authenticate(
            user=self.other_user
        )

        response = self.client.delete(
            f"/api/vibespace/moments/{moment.id}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            Moment.objects.filter(id=moment.id).exists()
        )

        mock_delete.assert_not_called()
