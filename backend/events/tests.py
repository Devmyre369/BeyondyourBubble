
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from events.models import Event
from hubs.models import Hub, HubMembership


User = get_user_model()


class EventDiscoveryAPITests(APITestCase):

    def setUp(self):
        self.owner = self.create_user("hub_owner")
        self.editor = self.create_user("hub_editor")
        self.member = self.create_user("hub_member")
        self.non_member = self.create_user("non_member")

        self.staff = self.create_user("byb_staff")
        self.staff.is_staff = True
        self.staff.save(update_fields=["is_staff"])

        self.hub = Hub.objects.create(
            name="Test Event Hub",
            slug="test-event-hub",
            hub_type=Hub.HubType.COMMUNITY,
            created_by=self.owner,
            owner=self.owner,
        )

        self.create_membership(
            self.owner,
            HubMembership.Role.OWNER,
        )
        self.create_membership(
            self.editor,
            HubMembership.Role.EDITOR,
        )
        self.create_membership(
            self.member,
            HubMembership.Role.MEMBER,
        )

        self.starts_at = timezone.now() + timedelta(days=7)
        self.ends_at = self.starts_at + timedelta(hours=3)

    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPassword123!",
            email_verified=True,
        )

    def create_membership(
        self,
        user,
        role,
        status=HubMembership.Status.APPROVED,
    ):
        return HubMembership.objects.create(
            hub=self.hub,
            user=user,
            role=role,
            status=status,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def event_payload(self, **overrides):
        payload = {
            "hub_id": str(self.hub.id),
            "title": "BYB Technical Summit",
            "description": "A technical community event.",
            "category": Event.Category.TECHNICAL,
            "starts_at": self.starts_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "format": Event.Format.OFFLINE,
            "venue_name": "Main Auditorium",
            "venue_address": "Lucknow, Uttar Pradesh",
            "city": "Lucknow",
        }
        payload.update(overrides)
        return payload

    def create_event(self, **overrides):
        defaults = {
            "organising_hub": self.hub,
            "created_by": self.owner,
            "title": "Approved Technical Summit",
            "description": "An approved technical event.",
            "category": Event.Category.TECHNICAL,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "format": Event.Format.OFFLINE,
            "venue_name": "Main Auditorium",
            "venue_address": "Lucknow",
            "city": "Lucknow",
            "status": Event.Status.PUBLISHED,
            "moderation_status": Event.ModerationStatus.APPROVED,
        }
        defaults.update(overrides)
        return Event.objects.create(**defaults)

    # --------------------------------------------------
    # EVENT SUBMISSION TESTS
    # --------------------------------------------------

    def test_owner_can_submit_event_for_moderation(self):
        self.authenticate(self.owner)

        response = self.client.post(
            "/api/events/",
            self.event_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        event = Event.objects.get(id=response.data["id"])

        self.assertEqual(event.organising_hub, self.hub)
        self.assertEqual(event.created_by, self.owner)
        self.assertEqual(event.status, Event.Status.DRAFT)
        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.PENDING,
        )
        self.assertIsNone(event.reviewed_by)
        self.assertIsNone(event.reviewed_at)

    def test_editor_can_submit_event(self):
        self.authenticate(self.editor)

        response = self.client.post(
            "/api/events/",
            self.event_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

    def test_member_cannot_submit_event(self):
        self.authenticate(self.member)

        response = self.client.post(
            "/api/events/",
            self.event_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_non_member_cannot_submit_event(self):
        self.authenticate(self.non_member)

        response = self.client.post(
            "/api/events/",
            self.event_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_pending_editor_cannot_submit_event(self):
        pending_editor = self.create_user("pending_editor")

        self.create_membership(
            pending_editor,
            HubMembership.Role.EDITOR,
            status=HubMembership.Status.PENDING,
        )

        self.authenticate(pending_editor)

        response = self.client.post(
            "/api/events/",
            self.event_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_inactive_hub_cannot_accept_event_submission(self):
        self.hub.is_active = False
        self.hub.save()

        self.authenticate(self.owner)

        response = self.client.post(
            "/api/events/",
            self.event_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_verified_hub_event_still_requires_moderation(self):
        self.hub.is_verified = True
        self.hub.save()

        self.authenticate(self.owner)

        response = self.client.post(
            "/api/events/",
            self.event_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        event = Event.objects.get(id=response.data["id"])

        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.PENDING,
        )
        self.assertEqual(event.status, Event.Status.DRAFT)

    def test_client_cannot_override_moderation_fields(self):
        self.authenticate(self.owner)

        payload = self.event_payload()
        payload["status"] = Event.Status.PUBLISHED
        payload["moderation_status"] = Event.ModerationStatus.APPROVED

        response = self.client.post(
            "/api/events/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        event = Event.objects.get(id=response.data["id"])

        self.assertEqual(event.status, Event.Status.DRAFT)
        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.PENDING,
        )

    # --------------------------------------------------
    # EVENT FORMAT VALIDATION TESTS
    # --------------------------------------------------

    def test_offline_event_requires_physical_venue(self):
        self.authenticate(self.owner)

        payload = self.event_payload(
            venue_name="",
            venue_address="",
            city="",
        )

        response = self.client.post(
            "/api/events/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("venue_name", response.data)
        self.assertIn("venue_address", response.data)
        self.assertIn("city", response.data)

    def test_online_event_requires_join_url(self):
        self.authenticate(self.owner)

        payload = self.event_payload(
            format=Event.Format.ONLINE,
            venue_name="",
            venue_address="",
            city="",
        )

        response = self.client.post(
            "/api/events/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("online_join_url", response.data)

    def test_online_event_can_be_submitted(self):
        self.authenticate(self.owner)

        payload = self.event_payload(
            format=Event.Format.ONLINE,
            venue_name="",
            venue_address="",
            city="",
            online_join_url="https://example.com/meeting",
            online_access_instructions="Join using the meeting link.",
        )

        response = self.client.post(
            "/api/events/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

    def test_hybrid_event_requires_physical_venue_and_join_url(self):
        self.authenticate(self.owner)

        payload = self.event_payload(
            format=Event.Format.HYBRID,
            online_join_url="",
        )

        response = self.client.post(
            "/api/events/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("online_join_url", response.data)

    def test_event_end_must_be_after_start(self):
        self.authenticate(self.owner)

        payload = self.event_payload(
            ends_at=(self.starts_at - timedelta(hours=1)).isoformat(),
        )

        response = self.client.post(
            "/api/events/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("ends_at", response.data)

    # --------------------------------------------------
    # PUBLIC EVENT DISCOVERY TESTS
    # --------------------------------------------------

    def test_discovery_returns_only_approved_published_events(self):
        self.create_event(title="Approved Event")

        self.create_event(
            title="Pending Event",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.create_event(
            title="Rejected Event",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.REJECTED,
        )

        self.create_event(
            title="Unapproved Published Event",
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.authenticate(self.non_member)

        response = self.client.get("/api/events/")

        self.assertEqual(response.status_code, 200)

        titles = [event["title"] for event in response.data]

        self.assertEqual(titles, ["Approved Event"])

    def test_discovery_excludes_events_from_inactive_hubs(self):
        inactive_hub = Hub.objects.create(
            name="Inactive Hub",
            slug="inactive-event-hub",
            hub_type=Hub.HubType.COMMUNITY,
            created_by=self.owner,
            owner=self.owner,
            is_active=False,
        )

        self.create_event(title="Active Hub Event")

        self.create_event(
            title="Inactive Hub Event",
            organising_hub=inactive_hub,
        )

        self.authenticate(self.non_member)

        response = self.client.get("/api/events/")

        self.assertEqual(response.status_code, 200)

        titles = [event["title"] for event in response.data]

        self.assertEqual(titles, ["Active Hub Event"])

    def test_online_join_details_are_public_in_v1(self):
        event = self.create_event(
            format=Event.Format.ONLINE,
            venue_name="",
            venue_address="",
            city="",
            online_join_url="https://example.com/meeting",
            online_access_instructions="Join at the scheduled time.",
        )

        self.authenticate(self.non_member)

        response = self.client.get(f"/api/events/{event.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["online_join_url"],
            "https://example.com/meeting",
        )
        self.assertEqual(
            response.data["online_access_instructions"],
            "Join at the scheduled time.",
        )

    def test_pending_event_cannot_be_retrieved_publicly(self):
        event = self.create_event(
            title="Pending Event",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.authenticate(self.non_member)

        response = self.client.get(f"/api/events/{event.id}/")

        self.assertEqual(response.status_code, 404)

    # --------------------------------------------------
    # STAFF MODERATION TESTS
    # --------------------------------------------------

    def test_staff_can_view_pending_moderation_queue(self):
        pending_event = self.create_event(
            title="Pending Review Event",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.create_event(title="Already Approved Event")

        self.authenticate(self.staff)

        response = self.client.get("/api/events/moderation/")

        self.assertEqual(response.status_code, 200)

        event_ids = [item["id"] for item in response.data]

        self.assertEqual(len(event_ids), 1)
        self.assertEqual(event_ids[0], str(pending_event.id))

    def test_non_staff_cannot_access_moderation_queue(self):
        self.authenticate(self.owner)

        response = self.client.get("/api/events/moderation/")

        self.assertEqual(response.status_code, 403)

    def test_staff_can_approve_pending_event(self):
        event = self.create_event(
            title="Event Awaiting Approval",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.authenticate(self.staff)

        response = self.client.post(
            f"/api/events/moderation/{event.id}/review/",
            {
                "decision": "approve",
                "review_notes": "Event details verified.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        event.refresh_from_db()

        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.APPROVED,
        )
        self.assertEqual(event.status, Event.Status.PUBLISHED)
        self.assertEqual(event.reviewed_by, self.staff)
        self.assertIsNotNone(event.reviewed_at)
        self.assertEqual(
            event.review_notes,
            "Event details verified.",
        )

    def test_staff_can_reject_pending_event(self):
        event = self.create_event(
            title="Event Awaiting Rejection",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.authenticate(self.staff)

        response = self.client.post(
            f"/api/events/moderation/{event.id}/review/",
            {
                "decision": "reject",
                "review_notes": "Insufficient event information.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        event.refresh_from_db()

        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.REJECTED,
        )
        self.assertEqual(event.status, Event.Status.DRAFT)
        self.assertEqual(event.reviewed_by, self.staff)
        self.assertIsNotNone(event.reviewed_at)
        self.assertEqual(
            event.review_notes,
            "Insufficient event information.",
        )

    def test_rejection_requires_review_reason(self):
        event = self.create_event(
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.authenticate(self.staff)

        response = self.client.post(
            f"/api/events/moderation/{event.id}/review/",
            {
                "decision": "reject",
                "review_notes": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        event.refresh_from_db()

        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.PENDING,
        )

    def test_non_staff_cannot_review_event(self):
        event = self.create_event(
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.authenticate(self.owner)

        response = self.client.post(
            f"/api/events/moderation/{event.id}/review/",
            {
                "decision": "approve",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        event.refresh_from_db()

        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.PENDING,
        )

    def test_already_reviewed_event_cannot_be_reviewed_again(self):
        event = self.create_event(
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.authenticate(self.staff)

        first_response = self.client.post(
            f"/api/events/moderation/{event.id}/review/",
            {
                "decision": "approve",
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, 200)

        second_response = self.client.post(
            f"/api/events/moderation/{event.id}/review/",
            {
                "decision": "reject",
                "review_notes": "Trying to reverse the decision.",
            },
            format="json",
        )

        self.assertEqual(second_response.status_code, 400)

        event.refresh_from_db()

        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.APPROVED,
        )
        self.assertEqual(event.status, Event.Status.PUBLISHED)
