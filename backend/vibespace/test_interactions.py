
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User, Profile
from vibespace.models import Vibe, Moment, Comment, Revibe, SavedContent


class VibeSpaceInteractionAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.owner = self.create_user("owner")
        self.other_user = self.create_user("other")
        self.private_user = self.create_user("private")

        self.create_profile(self.owner, Profile.Visibility.PUBLIC)
        self.create_profile(self.other_user, Profile.Visibility.PUBLIC)
        self.create_profile(self.private_user, Profile.Visibility.PRIVATE)

        self.vibe = Vibe.objects.create(
            author=self.owner,
            text="A public test Vibe",
        )

        self.moment = Moment.objects.create(
            author=self.owner,
            image_url="https://example.com/moment.png",
            cloudinary_public_id="byb/test/moment",
            caption="A public test Moment",
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

    # ==================================================
    # COMMENT TESTS
    # ==================================================

    def test_authenticated_user_can_comment_on_vibe(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            f"/api/vibespace/vibe/{self.vibe.id}/comments/",
            {"text": "Great Vibe!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

        comment = Comment.objects.first()
        self.assertEqual(comment.author, self.other_user)
        self.assertEqual(comment.vibe, self.vibe)
        self.assertIsNone(comment.moment)
        self.assertEqual(comment.text, "Great Vibe!")

    def test_authenticated_user_can_comment_on_moment(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            f"/api/vibespace/moment/{self.moment.id}/comments/",
            {"text": "Amazing Moment!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comment = Comment.objects.get()
        self.assertEqual(comment.moment, self.moment)
        self.assertIsNone(comment.vibe)

    def test_anonymous_user_cannot_comment(self):
        response = self.client.post(
            f"/api/vibespace/vibe/{self.vibe.id}/comments/",
            {"text": "Anonymous comment"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Comment.objects.count(), 0)

    def test_users_can_list_comments_on_visible_content(self):
        Comment.objects.create(
            author=self.other_user,
            vibe=self.vibe,
            text="Existing comment",
        )

        response = self.client.get(
            f"/api/vibespace/vibe/{self.vibe.id}/comments/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["text"], "Existing comment")

    def test_comment_author_can_edit_comment(self):
        comment = Comment.objects.create(
            author=self.other_user,
            vibe=self.vibe,
            text="Original comment",
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            f"/api/vibespace/comments/{comment.id}/",
            {"text": "Updated comment"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        comment.refresh_from_db()
        self.assertEqual(comment.text, "Updated comment")

    def test_other_user_cannot_edit_comment(self):
        comment = Comment.objects.create(
            author=self.owner,
            vibe=self.vibe,
            text="Original comment",
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            f"/api/vibespace/comments/{comment.id}/",
            {"text": "Unauthorized edit"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        comment.refresh_from_db()
        self.assertEqual(comment.text, "Original comment")

    def test_comment_author_can_delete_comment(self):
        comment = Comment.objects.create(
            author=self.other_user,
            vibe=self.vibe,
            text="Comment to delete",
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            f"/api/vibespace/comments/{comment.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    # ==================================================
    # REVIBE TESTS
    # ==================================================

    def test_user_can_create_direct_revibe(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            f"/api/vibespace/vibe/{self.vibe.id}/revibe/",
            {"revibe_type": "direct"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        revibe = Revibe.objects.get()
        self.assertEqual(revibe.author, self.other_user)
        self.assertEqual(revibe.vibe, self.vibe)
        self.assertEqual(revibe.revibe_type, Revibe.RevibeType.DIRECT)
        self.assertEqual(revibe.quote_text, "")

    def test_user_can_create_quote_revibe(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            f"/api/vibespace/moment/{self.moment.id}/revibe/",
            {
                "revibe_type": "quote",
                "quote_text": "This moment was unforgettable!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        revibe = Revibe.objects.get()
        self.assertEqual(revibe.moment, self.moment)
        self.assertEqual(revibe.revibe_type, Revibe.RevibeType.QUOTE)
        self.assertEqual(revibe.quote_text, "This moment was unforgettable!")

    def test_quote_revibe_requires_text(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            f"/api/vibespace/vibe/{self.vibe.id}/revibe/",
            {"revibe_type": "quote", "quote_text": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Revibe.objects.count(), 0)

    def test_direct_revibe_cannot_contain_quote_text(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            f"/api/vibespace/vibe/{self.vibe.id}/revibe/",
            {
                "revibe_type": "direct",
                "quote_text": "This should not be allowed",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Revibe.objects.count(), 0)

    def test_user_can_change_direct_revibe_to_quote_revibe(self):
        Revibe.objects.create(
            author=self.other_user,
            vibe=self.vibe,
            revibe_type=Revibe.RevibeType.DIRECT,
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            f"/api/vibespace/vibe/{self.vibe.id}/revibe/",
            {
                "revibe_type": "quote",
                "quote_text": "Adding my perspective",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Revibe.objects.count(), 1)

        revibe = Revibe.objects.get()
        self.assertEqual(revibe.revibe_type, Revibe.RevibeType.QUOTE)
        self.assertEqual(revibe.quote_text, "Adding my perspective")

    def test_repeated_revibe_does_not_create_duplicate(self):
        self.client.force_authenticate(user=self.other_user)

        url = f"/api/vibespace/vibe/{self.vibe.id}/revibe/"

        first_response = self.client.post(
            url,
            {"revibe_type": "direct"},
            format="json",
        )

        second_response = self.client.post(
            url,
            {"revibe_type": "direct"},
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(Revibe.objects.count(), 1)

    def test_user_can_remove_own_revibe(self):
        Revibe.objects.create(
            author=self.other_user,
            vibe=self.vibe,
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            f"/api/vibespace/vibe/{self.vibe.id}/revibe/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Revibe.objects.count(), 0)

    def test_user_cannot_revibe_private_content(self):
        private_vibe = Vibe.objects.create(
            author=self.private_user,
            text="Private Vibe",
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            f"/api/vibespace/vibe/{private_vibe.id}/revibe/",
            {"revibe_type": "direct"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Revibe.objects.count(), 0)

    # ==================================================
    # SAVED CONTENT TESTS
    # ==================================================

    def test_user_can_save_vibe(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            "/api/vibespace/saved/",
            {"vibe": str(self.vibe.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SavedContent.objects.count(), 1)

        saved = SavedContent.objects.get()
        self.assertEqual(saved.user, self.other_user)
        self.assertEqual(saved.vibe, self.vibe)
        self.assertIsNone(saved.moment)

    def test_user_can_save_moment(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            "/api/vibespace/saved/",
            {"moment": str(self.moment.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        saved = SavedContent.objects.get()
        self.assertEqual(saved.moment, self.moment)
        self.assertIsNone(saved.vibe)

    def test_user_cannot_save_both_vibe_and_moment_together(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            "/api/vibespace/saved/",
            {
                "vibe": str(self.vibe.id),
                "moment": str(self.moment.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SavedContent.objects.count(), 0)

    def test_duplicate_save_does_not_create_duplicate(self):
        self.client.force_authenticate(user=self.other_user)

        url = "/api/vibespace/saved/"
        data = {"vibe": str(self.vibe.id)}

        first_response = self.client.post(url, data, format="json")
        second_response = self.client.post(url, data, format="json")

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(SavedContent.objects.count(), 1)

    def test_user_can_list_own_saved_content(self):
        SavedContent.objects.create(
            user=self.other_user,
            vibe=self.vibe,
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.get("/api/vibespace/saved/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_user_cannot_list_another_users_saved_content(self):
        SavedContent.objects.create(
            user=self.owner,
            vibe=self.vibe,
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.get("/api/vibespace/saved/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_user_can_remove_saved_content(self):
        saved = SavedContent.objects.create(
            user=self.other_user,
            vibe=self.vibe,
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            f"/api/vibespace/saved/{saved.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SavedContent.objects.filter(id=saved.id).exists())

    def test_user_cannot_remove_another_users_saved_content(self):
        saved = SavedContent.objects.create(
            user=self.owner,
            vibe=self.vibe,
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            f"/api/vibespace/saved/{saved.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(SavedContent.objects.filter(id=saved.id).exists())

    def test_user_cannot_save_private_content(self):
        private_vibe = Vibe.objects.create(
            author=self.private_user,
            text="Private Vibe",
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            "/api/vibespace/saved/",
            {"vibe": str(private_vibe.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(SavedContent.objects.count(), 0)
