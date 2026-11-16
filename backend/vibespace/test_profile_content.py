from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import Follow, Profile, User
from vibespace.models import Moment, Vibe


class ProfileContentApiTests(APITestCase):
    def setUp(self):
        self.viewer = self.create_user("viewer")
        self.author = self.create_user("author")
        self.private_user = self.create_user("private_author", "private")

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

    def test_posts_combine_vibes_and_moments_newest_first(self):
        now = timezone.now()
        older_vibe = Vibe.objects.create(
            author=self.author,
            text="Older Vibe",
        )
        moment = Moment.objects.create(
            author=self.author,
            image_url="https://example.com/moment.jpg",
            caption="A Moment",
        )
        newer_vibe = Vibe.objects.create(
            author=self.author,
            text="Newer Vibe",
        )
        Vibe.objects.filter(pk=older_vibe.pk).update(
            created_at=now - timedelta(minutes=3)
        )
        Moment.objects.filter(pk=moment.pk).update(
            created_at=now - timedelta(minutes=2)
        )
        Vibe.objects.filter(pk=newer_vibe.pk).update(
            created_at=now - timedelta(minutes=1)
        )
        Follow.objects.create(follower=self.viewer, following=self.author)
        self.client.force_authenticate(self.viewer)

        response = self.client.get(
            "/api/vibespace/profiles/author/posts/?page=1"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(
            [entry["content_text"] for entry in response.data["results"]],
            ["Newer Vibe", "A Moment", "Older Vibe"],
        )
        self.assertEqual(
            [entry["content_type"] for entry in response.data["results"]],
            ["vibe", "moment", "vibe"],
        )
        self.assertTrue(response.data["results"][0]["is_following"])
        self.assertEqual(
            response.data["results"][0]["author_username"],
            "author",
        )
        self.assertNotIn("email", response.data["results"][0])

    def test_profile_vibes_and_moments_support_pagination_without_changing_legacy_shape(self):
        for index in range(12):
            Vibe.objects.create(
                author=self.author,
                text=f"Vibe {index}",
            )
        for index in range(11):
            Moment.objects.create(
                author=self.author,
                image_url=f"https://example.com/{index}.jpg",
                caption=f"Moment {index}",
            )

        vibes_page_one = self.client.get(
            "/api/vibespace/vibes/?username=author&page=1"
        )
        vibes_page_two = self.client.get(
            "/api/vibespace/vibes/?username=author&page=2"
        )
        moments_page_one = self.client.get(
            "/api/vibespace/moments/?username=author&page=1"
        )
        legacy_vibes = self.client.get(
            "/api/vibespace/vibes/?username=author"
        )

        self.assertEqual(vibes_page_one.data["count"], 12)
        self.assertEqual(len(vibes_page_one.data["results"]), 10)
        self.assertEqual(vibes_page_one.data["next"], 2)
        self.assertEqual(len(vibes_page_two.data["results"]), 2)
        self.assertEqual(moments_page_one.data["count"], 11)
        self.assertEqual(len(moments_page_one.data["results"]), 10)
        self.assertEqual(moments_page_one.data["next"], 2)
        self.assertEqual(len(legacy_vibes.data), 12)

    def test_private_profile_posts_are_not_publicly_accessible(self):
        Vibe.objects.create(
            author=self.private_user,
            text="Private Vibe",
        )
        Moment.objects.create(
            author=self.private_user,
            image_url="https://example.com/private.jpg",
        )

        posts = self.client.get(
            "/api/vibespace/profiles/private_author/posts/"
        )
        vibes = self.client.get(
            "/api/vibespace/vibes/?username=private_author&page=1"
        )
        moments = self.client.get(
            "/api/vibespace/moments/?username=private_author&page=1"
        )

        self.assertEqual(posts.status_code, 404)
        self.assertEqual(vibes.data["count"], 0)
        self.assertEqual(moments.data["count"], 0)
