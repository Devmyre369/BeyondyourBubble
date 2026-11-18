
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Profile
from events.models import Event
from hubs.models import Hub
from vibespace.models import Moment, Vibe


User = get_user_model()


class GlobalSearchTests(APITestCase):
    def setUp(self):
        self.searcher = User.objects.create_user(
            username="searcher",
            email="searcher@example.com",
            password="TestPassword123!",
            email_verified=True,
        )
        self.authenticate_as(self.searcher)

    def authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def create_user_with_profile(
        self,
        username,
        visibility=Profile.Visibility.PUBLIC,
        **user_fields,
    ):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPassword123!",
            email_verified=True,
            **user_fields,
        )
        Profile.objects.create(
            user=user,
            profile_type=Profile.ProfileType.STUDENT,
            visibility=visibility,
            bio="Robotics enthusiast",
        )
        return user

    def test_search_returns_public_posts_users_events_and_hubs(self):
        author = self.create_user_with_profile(
            "robotics_member",
            first_name="Riya",
            last_name="Shah",
        )

        event_hub = Hub.objects.create(
            name="Robotics Event Hub",
            slug="robotics-event-hub",
            hub_type=Hub.HubType.COMMUNITY,
            created_by=author,
            owner=author,
        )

        event = Event.objects.create(
            organising_hub=event_hub,
            created_by=author,
            title="Robotics Day",
            description="A campus robotics event.",
            city="Lucknow",
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.APPROVED,
        )

        Vibe.objects.create(
            author=author,
            event=event,
            text="Building a robotics project.",
        )

        Moment.objects.create(
            author=author,
            event=event,
            image_url="https://example.com/robotics.png",
            caption="Robotics demonstration",
        )

        Hub.objects.create(
            name="Robotics Hub",
            slug="robotics-hub",
            hub_type=Hub.HubType.COMMUNITY,
            short_description="Robotics community",
            created_by=author,
            owner=author,
        )

        response = self.client.get("/api/search/?q=robotics")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["query"], "robotics")
        self.assertEqual(
            set(response.data["results"]),
            {"posts", "users", "events", "hubs"},
        )
        self.assertEqual(
            {post["content_type"] for post in response.data["results"]["posts"]},
            {"vibe", "moment"},
        )
        self.assertEqual(
            response.data["results"]["users"][0]["username"],
            "robotics_member",
        )
        self.assertEqual(
            response.data["results"]["events"][0]["title"],
            "Robotics Day",
        )
        self.assertEqual(
            response.data["results"]["hubs"][0]["name"],
            "Robotics Hub",
        )
        self.assertNotIn("email", response.data["results"]["users"][0])

    def test_search_respects_private_profiles_and_feed_visibility(self):
        private_user = self.create_user_with_profile(
            "private_robotics",
            visibility=Profile.Visibility.PRIVATE,
        )
        public_user = self.create_user_with_profile("public_author")

        Vibe.objects.create(
            author=private_user,
            text="Secret robotics post",
        )
        Vibe.objects.create(
            author=public_user,
            text="Public robotics post",
        )
        Vibe.objects.create(
            author=self.searcher,
            text="My robotics post",
        )

        response = self.client.get("/api/search/?q=robotics")

        self.assertEqual(response.status_code, 200)

        usernames = {
            user["username"]
            for user in response.data["results"]["users"]
        }
        post_authors = {
            post["author_username"]
            for post in response.data["results"]["posts"]
        }

        self.assertNotIn("private_robotics", usernames)
        self.assertNotIn("private_robotics", post_authors)
        self.assertIn("public_author", post_authors)
        self.assertIn("searcher", post_authors)

    def test_search_excludes_unpublished_events_and_inactive_hubs(self):
        organizer = self.create_user_with_profile("event_organizer")

        event_hub = Hub.objects.create(
            name="Event Test Hub",
            slug="event-test-hub",
            hub_type=Hub.HubType.COMMUNITY,
            created_by=organizer,
            owner=organizer,
        )

        Event.objects.create(
            organising_hub=event_hub,
            created_by=organizer,
            title="Robotics draft",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        Event.objects.create(
            organising_hub=event_hub,
            created_by=organizer,
            title="Robotics published",
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.APPROVED,
        )

        Hub.objects.create(
            name="Active Robotics Hub",
            slug="active-robotics-hub",
            hub_type=Hub.HubType.COMMUNITY,
            created_by=organizer,
            owner=organizer,
        )

        Hub.objects.create(
            name="Inactive Robotics Hub",
            slug="inactive-robotics-hub",
            hub_type=Hub.HubType.COMMUNITY,
            created_by=organizer,
            owner=organizer,
            is_active=False,
        )

        response = self.client.get("/api/search/?q=robotics")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [event["title"] for event in response.data["results"]["events"]],
            ["Robotics published"],
        )
        self.assertEqual(
            [hub["name"] for hub in response.data["results"]["hubs"]],
            ["Active Robotics Hub"],
        )

    def test_search_category_pagination_and_counts(self):
        owner = self.create_user_with_profile("hub_owner")

        for index in range(12):
            Hub.objects.create(
                name=f"Robotics Hub {index}",
                slug=f"robotics-hub-{index}",
                hub_type=Hub.HubType.COMMUNITY,
                created_by=owner,
                owner=owner,
            )

        response = self.client.get(
            "/api/search/?q=robotics&category=hubs&page=2&page_size=5"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["counts"]["hubs"], 12)
        self.assertEqual(len(response.data["results"]["hubs"]), 5)
        self.assertTrue(response.data["has_more"]["hubs"])
        self.assertEqual(response.data["results"]["users"], [])

    def test_search_requires_authentication_and_valid_parameters(self):
        self.client.credentials()

        unauthenticated = self.client.get("/api/search/?q=robotics")
        self.assertEqual(unauthenticated.status_code, 401)

        self.authenticate_as(self.searcher)

        for query in ("", "a"):
            with self.subTest(query=query):
                invalid_query = self.client.get(
                    "/api/search/",
                    {"q": query},
                )
                self.assertEqual(invalid_query.status_code, 400)
                self.assertIn("q", invalid_query.data)

        invalid_category = self.client.get(
            "/api/search/?q=robotics&category=unknown"
        )
        self.assertEqual(invalid_category.status_code, 400)
        self.assertIn("category", invalid_category.data)

        invalid_page_size = self.client.get(
            "/api/search/?q=robotics&page_size=21"
        )
        self.assertEqual(invalid_page_size.status_code, 400)
        self.assertIn("page_size", invalid_page_size.data)
