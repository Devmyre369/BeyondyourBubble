from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Follow, Profile, User


class FollowApiTests(APITestCase):
    def setUp(self):
        self.viewer = self.create_user("viewer")
        self.target = self.create_user("target")
        self.private_user = self.create_user("private_target", "private")
        self.follow_url = "/api/accounts/profile/target/follow/"

    def create_user(self, username, visibility=Profile.Visibility.PUBLIC):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPassword123!",
            email_verified=True,
        )
        Profile.objects.create(
            user=user,
            profile_type=Profile.ProfileType.STUDENT,
            visibility=visibility,
        )
        return user

    def test_follow_is_idempotent_and_returns_current_counts(self):
        self.client.force_authenticate(self.viewer)

        first = self.client.post(self.follow_url)
        duplicate = self.client.post(self.follow_url)

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(duplicate.status_code, status.HTTP_200_OK)
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(first.data["is_following"], True)
        self.assertEqual(first.data["followers_count"], 1)
        self.assertEqual(first.data["viewer_following_count"], 1)

        relationship = self.client.get(self.follow_url)
        self.assertEqual(relationship.status_code, status.HTTP_200_OK)
        self.assertTrue(relationship.data["is_following"])

    def test_user_cannot_follow_themselves(self):
        self.client.force_authenticate(self.viewer)

        response = self.client.post(
            f"/api/accounts/profile/{self.viewer.username}/follow/"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_and_unfollow_require_authentication(self):
        response = self.client.post(self.follow_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.delete(self.follow_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_repeated_unfollow_is_safe(self):
        self.client.force_authenticate(self.viewer)
        self.client.post(self.follow_url)

        first = self.client.delete(self.follow_url)
        second = self.client.delete(self.follow_url)

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertFalse(second.data["is_following"])
        self.assertEqual(second.data["followers_count"], 0)
        self.assertEqual(Follow.objects.count(), 0)

    def test_private_profiles_are_not_available_through_social_apis(self):
        self.client.force_authenticate(self.viewer)

        profile = self.client.get(
            "/api/accounts/profile/private_target/"
        )
        follow = self.client.post(
            "/api/accounts/profile/private_target/follow/"
        )
        followers = self.client.get(
            "/api/accounts/profile/private_target/followers/"
        )

        self.assertEqual(profile.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(follow.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(followers.status_code, status.HTTP_404_NOT_FOUND)

    def test_profile_overview_has_real_counts_and_no_private_account_fields(self):
        from vibespace.models import Moment, Vibe

        Profile.objects.filter(user=self.target).update(
            byb_signature="Beyond the ordinary"
        )
        Vibe.objects.create(author=self.target, text="A public Vibe")
        Moment.objects.create(
            author=self.target,
            image_url="https://example.com/photo.jpg",
            caption="A public Moment",
        )
        Follow.objects.create(follower=self.viewer, following=self.target)
        self.client.force_authenticate(self.viewer)

        response = self.client.get(
            "/api/accounts/profile/target/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["statistics"],
            {
                "vibes_count": 1,
                "moments_count": 1,
                "posts_count": 2,
                "followers_count": 1,
                "following_count": 0,
            },
        )
        self.assertTrue(response.data["is_following"])
        self.assertNotIn("email", response.data["profile"])
        self.assertNotIn("password", response.data["profile"])

    def test_followers_and_following_return_safe_paginated_users(self):
        second = self.create_user("second_follower")
        self.client.force_authenticate(self.viewer)
        Follow.objects.create(follower=self.viewer, following=self.target)
        Follow.objects.create(follower=second, following=self.target)
        Follow.objects.create(follower=self.target, following=second)

        followers = self.client.get(
            "/api/accounts/profile/target/followers/"
        )
        following = self.client.get(
            "/api/accounts/profile/target/following/"
        )

        self.assertEqual(followers.status_code, status.HTTP_200_OK)
        self.assertEqual(followers.data["count"], 2)
        self.assertEqual(
            {item["username"] for item in followers.data["results"]},
            {self.viewer.username, second.username},
        )
        self.assertEqual(following.data["count"], 1)
        self.assertEqual(
            following.data["results"][0]["username"],
            second.username,
        )
        self.assertNotIn("email", following.data["results"][0])

    def test_connection_lists_are_paginated(self):
        self.client.force_authenticate(self.viewer)
        for index in range(21):
            user = self.create_user(f"follower_{index}")
            Follow.objects.create(follower=user, following=self.target)

        first = self.client.get(
            "/api/accounts/profile/target/followers/?page=1"
        )
        second = self.client.get(
            "/api/accounts/profile/target/followers/?page=2"
        )

        self.assertEqual(first.data["count"], 21)
        self.assertEqual(len(first.data["results"]), 20)
        self.assertEqual(first.data["next"], 2)
        self.assertEqual(len(second.data["results"]), 1)
        self.assertIsNone(second.data["next"])
