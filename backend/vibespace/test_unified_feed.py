from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import Profile
from events.models import Event
from hubs.models import Hub
from vibespace.models import Moment, Vibe


User = get_user_model()


class UnifiedFeedTests(APITestCase):
    def setUp(self):
        self.viewer = self.create_user("feed_viewer")
        self.public_user = self.create_user("feed_public")
        self.private_user = self.create_user("feed_private")
        self.inactive_user = self.create_user("feed_inactive")
        self.create_profile(self.viewer, Profile.Visibility.PRIVATE)
        self.create_profile(self.public_user, Profile.Visibility.PUBLIC)
        self.create_profile(self.private_user, Profile.Visibility.PRIVATE)
        self.create_profile(self.inactive_user, Profile.Visibility.PUBLIC)
        self.inactive_user.is_active = False
        self.inactive_user.save(update_fields=["is_active"])

        self.hub = Hub.objects.create(
            name="Feed Hub",
            slug="feed-hub",
            hub_type=Hub.HubType.COMMUNITY,
            created_by=self.public_user,
            owner=self.public_user,
        )
        self.client.force_authenticate(user=self.viewer)

    @staticmethod
    def create_user(username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPassword123!",
            email_verified=True,
        )

    @staticmethod
    def create_profile(user, visibility):
        return Profile.objects.create(
            user=user,
            profile_type=Profile.ProfileType.STUDENT,
            visibility=visibility,
        )

    def create_event(self, **overrides):
        values = {
            "organising_hub": self.hub,
            "created_by": self.public_user,
            "title": "Community event",
            "description": "Meet the BYB community.",
            "starts_at": timezone.now() + timedelta(days=2),
            "ends_at": timezone.now() + timedelta(days=2, hours=2),
            "venue_name": "Community Hall",
            "city": "Delhi",
            "status": Event.Status.PUBLISHED,
            "moderation_status": Event.ModerationStatus.APPROVED,
        }
        values.update(overrides)
        return Event.objects.create(**values)

    def test_feed_combines_all_content_types_in_chronological_order(self):
        base = timezone.now() - timedelta(minutes=5)
        vibe = Vibe.objects.create(author=self.public_user, text="A text post")
        moment = Moment.objects.create(
            author=self.public_user,
            image_url="https://example.com/moment.jpg",
            caption="A photo post",
        )
        event = self.create_event()
        Vibe.objects.filter(pk=vibe.pk).update(created_at=base + timedelta(minutes=1))
        Moment.objects.filter(pk=moment.pk).update(created_at=base + timedelta(minutes=2))
        Event.objects.filter(pk=event.pk).update(created_at=base + timedelta(minutes=3))

        response = self.client.get("/api/vibespace/feed/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["content_type"] for item in response.data["results"]],
            ["event", "moment", "vibe"],
        )
        event_entry = response.data["results"][0]
        self.assertEqual(event_entry["event_id"], str(event.id))
        self.assertEqual(event_entry["event_title"], event.title)
        self.assertEqual(event_entry["event_hub_id"], str(self.hub.id))
        self.assertEqual(event_entry["event_hub_name"], self.hub.name)

    def test_feed_paginates_mixed_items_without_overlap(self):
        base = timezone.now() - timedelta(hours=1)
        entries = []
        for index in range(12):
            entries.append(("vibe", Vibe.objects.create(author=self.public_user, text=f"Vibe {index}")))
            entries.append(("moment", Moment.objects.create(
                author=self.public_user,
                image_url=f"https://example.com/{index}.jpg",
                caption=f"Moment {index}",
            )))
            entries.append(("event", self.create_event(title=f"Event {index}")))
        for index, (kind, item) in enumerate(entries):
            model = {"vibe": Vibe, "moment": Moment, "event": Event}[kind]
            model.objects.filter(pk=item.pk).update(created_at=base + timedelta(seconds=index))

        first = self.client.get("/api/vibespace/feed/?page=1")
        second = self.client.get("/api/vibespace/feed/?page=2")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        first_keys = {(item["content_type"], item["id"]) for item in first.data["results"]}
        second_keys = {(item["content_type"], item["id"]) for item in second.data["results"]}
        self.assertEqual(len(first.data["results"]), 10)
        self.assertEqual(len(second.data["results"]), 10)
        self.assertFalse(first_keys & second_keys)
        self.assertEqual(first.data["count"], 36)

    def test_feed_excludes_private_inactive_unverified_and_unpublished_content(self):
        own_private = Vibe.objects.create(author=self.viewer, text="My private Vibe")
        Vibe.objects.create(author=self.private_user, text="Private content")
        Vibe.objects.create(author=self.inactive_user, text="Inactive author")
        unverified = self.create_user("feed_unverified")
        self.create_profile(unverified, Profile.Visibility.PUBLIC)
        unverified.email_verified = False
        unverified.save(update_fields=["email_verified"])
        Moment.objects.create(
            author=unverified,
            image_url="https://example.com/private.jpg",
            caption="Unverified author",
        )
        self.create_event(title="Pending event", moderation_status=Event.ModerationStatus.PENDING)
        self.create_event(title="Draft event", status=Event.Status.DRAFT)
        published = self.create_event(title="Visible event")

        response = self.client.get("/api/vibespace/feed/")

        self.assertEqual(response.status_code, 200)
        titles = [item["event_title"] for item in response.data["results"]]
        texts = [item["content_text"] for item in response.data["results"]]
        self.assertIn(published.title, titles)
        self.assertNotIn("Pending event", titles)
        self.assertNotIn("Draft event", titles)
        self.assertNotIn("Private content", texts)
        self.assertNotIn("Inactive author", texts)
        self.assertNotIn("Unverified author", texts)
        self.assertIn(own_private.text, texts)

    def test_hidden_associated_event_does_not_leak_through_post_context(self):
        hidden_event = self.create_event(
            title="Rejected event",
            moderation_status=Event.ModerationStatus.REJECTED,
        )
        vibe = Vibe.objects.create(
            author=self.public_user,
            text="Still visible experience",
            event=hidden_event,
        )

        response = self.client.get("/api/vibespace/feed/")
        item = next(row for row in response.data["results"] if row["id"] == str(vibe.id))

        self.assertEqual(item["content_text"], vibe.text)
        self.assertIsNone(item["event_id"])
        self.assertIsNone(item["event_title"])
