
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import Notification
from events.models import Event, EventModerationReview
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

        self.create_membership(self.owner, HubMembership.Role.OWNER)
        self.create_membership(self.editor, HubMembership.Role.EDITOR)
        self.create_membership(self.member, HubMembership.Role.MEMBER)

        self.starts_at = timezone.now() + timedelta(days=7)
        self.ends_at = self.starts_at + timedelta(hours=3)

    # --------------------------------------------------
    # TEST HELPERS
    # --------------------------------------------------

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

    def test_submission_notifies_staff_and_other_hub_managers_once(self):
        self.authenticate(self.editor)
        response = self.client.post(
            "/api/events/", self.event_payload(), format="json",
        )
        event = Event.objects.get(pk=response.data["id"])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.filter(
            recipient=self.owner,
            event=event,
            verb=Notification.Verb.EVENT_SUBMITTED,
        ).count(), 1)
        self.assertEqual(Notification.objects.filter(
            recipient=self.staff,
            event=event,
            verb=Notification.Verb.EVENT_SUBMITTED,
        ).count(), 1)

    def test_moderation_notifies_submitter_and_hub_managers(self):
        event = Event.objects.create(
            organising_hub=self.hub,
            created_by=self.editor,
            title="Moderated Event",
            category=Event.Category.TECHNICAL,
            starts_at=self.starts_at,
            ends_at=self.ends_at,
            format=Event.Format.OFFLINE,
            venue_name="Hall",
            venue_address="Road",
            city="Lucknow",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )
        self.authenticate(self.staff)
        response = self.client.post(
            f"/api/events/moderation/{event.id}/review/",
            {"decision": "approve"}, format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(
            recipient=self.editor,
            event=event,
            verb=Notification.Verb.EVENT_APPROVED,
        ).count(), 1)
        self.assertEqual(Notification.objects.filter(
            recipient=self.owner,
            event=event,
            verb=Notification.Verb.EVENT_APPROVED,
        ).count(), 1)

    def test_event_notifications_do_not_expose_inaccessible_pending_event(self):
        event = Event.objects.create(
            organising_hub=self.hub,
            created_by=self.owner,
            title="Private Pending Event",
            category=Event.Category.TECHNICAL,
            starts_at=self.starts_at,
            ends_at=self.ends_at,
            format=Event.Format.OFFLINE,
            venue_name="Hall",
            venue_address="Road",
            city="Lucknow",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )
        Notification.objects.create(
            recipient=self.non_member,
            actor=self.staff,
            verb=Notification.Verb.EVENT_SUBMITTED,
            event=event,
            hub=self.hub,
        )
        self.authenticate(self.non_member)
        response = self.client.get("/api/accounts/notifications/")
        item = response.data["results"][0]
        self.assertIsNone(item["event_id"])
        self.assertIsNone(item["event_title"])

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

    def test_hub_manager_cannot_review_an_event(self):
        event = self.create_event(
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )
        self.authenticate(self.owner)

        response = self.client.post(
            f"/api/events/moderation/{event.id}/review/",
            {"decision": "approve"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        event.refresh_from_db()
        self.assertEqual(event.moderation_status, Event.ModerationStatus.PENDING)
        self.assertFalse(EventModerationReview.objects.filter(event=event).exists())

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

        results = response.data["results"]
        titles = [event["title"] for event in results]

        self.assertEqual(titles, ["Approved Event"])
        self.assertEqual(response.data["count"], 1)

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

        results = response.data["results"]
        titles = [event["title"] for event in results]

        self.assertEqual(titles, ["Active Hub Event"])
        self.assertEqual(response.data["count"], 1)

    def test_discovery_response_uses_default_page_size(self):
        for index in range(13):
            self.create_event(title=f"Paginated Event {index}")

        self.authenticate(self.non_member)

        response = self.client.get("/api/events/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 13)
        self.assertEqual(len(response.data["results"]), 12)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_discovery_supports_custom_page_size(self):
        for index in range(3):
            self.create_event(title=f"Custom Size Event {index}")

        self.authenticate(self.non_member)

        first_page = self.client.get("/api/events/?page_size=2")
        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data["count"], 3)
        self.assertEqual(len(first_page.data["results"]), 2)
        self.assertIsNotNone(first_page.data["next"])
        self.assertIsNone(first_page.data["previous"])

        second_page = self.client.get("/api/events/?page_size=2&page=2")
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(second_page.data["count"], 3)
        self.assertEqual(len(second_page.data["results"]), 1)
        self.assertIsNone(second_page.data["next"])
        self.assertIsNotNone(second_page.data["previous"])

    def test_discovery_enforces_maximum_page_size(self):
        for index in range(51):
            self.create_event(title=f"Large Page Event {index}")

        self.authenticate(self.non_member)

        response = self.client.get("/api/events/?page_size=100")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 51)
        self.assertEqual(len(response.data["results"]), 50)

    def test_discovery_filters_still_apply_with_pagination(self):
        self.create_event(
            title="Cultural Event",
            category=Event.Category.CULTURAL,
            city="Delhi",
        )
        self.create_event(
            title="Technical Event",
            category=Event.Category.TECHNICAL,
            city="Lucknow",
        )
        self.create_event(
            title="Another Technical Event",
            category=Event.Category.TECHNICAL,
            city="Lucknow",
        )

        self.authenticate(self.non_member)

        response = self.client.get(
            "/api/events/?category=technical&city=Lucknow&page_size=1"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next"])

    def test_event_choices_returns_plain_list(self):
        event = self.create_event(created_by=self.owner)

        self.authenticate(self.owner)

        response = self.client.get("/api/events/choices/")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(event.id))

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

    def test_approved_event_can_be_retrieved_by_authenticated_user(self):
        event = self.create_event()
        self.authenticate(self.non_member)

        response = self.client.get(f"/api/events/{event.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(event.id))

    def test_inactive_hub_event_is_not_publicly_visible(self):
        event = self.create_event()
        self.hub.is_active = False
        self.hub.save(update_fields=["is_active"])
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

        results = response.data["results"]
        event_ids = [item["id"] for item in results]

        self.assertEqual(len(event_ids), 1)
        self.assertEqual(event_ids[0], str(pending_event.id))
        self.assertEqual(response.data["count"], 1)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

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
        review = EventModerationReview.objects.get(event=event)
        self.assertEqual(review.reviewer, self.staff)
        self.assertEqual(review.decision, EventModerationReview.Decision.APPROVED)
        self.assertEqual(review.review_notes, "Event details verified.")

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
        self.assertTrue(
            EventModerationReview.objects.filter(
                event=event,
                reviewer=self.staff,
                decision=EventModerationReview.Decision.REJECTED,
                review_notes="Insufficient event information.",
            ).exists()
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

    # --------------------------------------------------
    # HUB EVENT MANAGEMENT TESTS
    # --------------------------------------------------

    def test_owner_can_view_all_hub_events(self):
        self.create_event(
            title="Pending Event",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.create_event(
            title="Rejected Event",
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.REJECTED,
            reviewed_by=self.staff,
            reviewed_at=timezone.now(),
            review_notes="Needs changes",
        )
        rejected_event = Event.objects.get(title="Rejected Event")
        EventModerationReview.objects.create(
            event=rejected_event,
            reviewer=self.staff,
            decision=EventModerationReview.Decision.REJECTED,
            review_notes="Needs changes",
        )

        self.create_event(title="Published Event")

        self.authenticate(self.owner)

        response = self.client.get(
            f"/api/events/hubs/{self.hub.id}/"
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(results), 3)

        rejected_event = next(
            event for event in results
            if event["title"] == "Rejected Event"
        )

        self.assertEqual(
            rejected_event["review_notes"],
            "Needs changes",
        )
        self.assertEqual(len(rejected_event["moderation_history"]), 1)
        self.assertEqual(
            rejected_event["moderation_history"][0]["reviewer_username"],
            self.staff.username,
        )

    def test_hub_event_management_supports_page_size(self):
        for index in range(3):
            self.create_event(title=f"Hub Event {index}")

        self.authenticate(self.owner)

        first_page = self.client.get(
            f"/api/events/hubs/{self.hub.id}/?page_size=2"
        )

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data["count"], 3)
        self.assertEqual(len(first_page.data["results"]), 2)
        self.assertIsNotNone(first_page.data["next"])
        self.assertIsNone(first_page.data["previous"])

        second_page = self.client.get(
            f"/api/events/hubs/{self.hub.id}/?page_size=2&page=2"
        )

        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(second_page.data["count"], 3)
        self.assertEqual(len(second_page.data["results"]), 1)
        self.assertIsNone(second_page.data["next"])
        self.assertIsNotNone(second_page.data["previous"])

    def test_editor_can_manage_event_created_by_another_hub_member(self):
        event = self.create_event(
            created_by=self.owner,
            title="Original Event",
        )

        self.authenticate(self.editor)

        response = self.client.patch(
            f"/api/events/manage/{event.id}/",
            {"title": "Updated Event"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Updated Event")

    def test_member_cannot_view_hub_event_management(self):
        self.authenticate(self.member)

        response = self.client.get(
            f"/api/events/hubs/{self.hub.id}/"
        )

        self.assertEqual(response.status_code, 403)

    def test_non_member_cannot_view_hub_event_management(self):
        self.authenticate(self.non_member)

        response = self.client.get(
            f"/api/events/hubs/{self.hub.id}/"
        )

        self.assertEqual(response.status_code, 403)

    def test_manager_cannot_access_another_hubs_events(self):
        another_hub = Hub.objects.create(
            name="Another Hub",
            slug="another-hub",
            description="Another test hub",
            created_by=self.non_member,
            owner=self.non_member,
        )

        event = self.create_event(
            organising_hub=another_hub,
            title="Another Hub Event",
        )

        self.authenticate(self.owner)

        response = self.client.get(
            f"/api/events/manage/{event.id}/"
        )

        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------
    # EVENT MODIFICATION AND MODERATION RESET TESTS
    # --------------------------------------------------

    def test_editing_approved_event_resets_moderation(self):
        event = self.create_event(
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.APPROVED,
            reviewed_by=self.staff,
            reviewed_at=timezone.now(),
            review_notes="Approved",
        )
        EventModerationReview.objects.create(
            event=event,
            reviewer=self.staff,
            decision=EventModerationReview.Decision.APPROVED,
            review_notes="Approved",
        )

        self.authenticate(self.owner)

        response = self.client.patch(
            f"/api/events/manage/{event.id}/",
            {"title": "Updated Approved Event"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        event.refresh_from_db()

        self.assertEqual(event.status, Event.Status.DRAFT)
        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.PENDING,
        )
        self.assertEqual(event.reviewed_by, self.staff)
        self.assertIsNotNone(event.reviewed_at)
        self.assertEqual(event.review_notes, "Approved")
        self.assertEqual(event.moderation_history.count(), 1)
        self.assertTrue(Notification.objects.filter(
            recipient=self.editor,
            event=event,
            verb=Notification.Verb.EVENT_UPDATED,
        ).exists())

    def test_editing_rejected_event_resubmits_for_moderation(self):
        event = self.create_event(
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.REJECTED,
            reviewed_by=self.staff,
            reviewed_at=timezone.now(),
            review_notes="Please correct the event details.",
        )
        EventModerationReview.objects.create(
            event=event,
            reviewer=self.staff,
            decision=EventModerationReview.Decision.REJECTED,
            review_notes="Please correct the event details.",
        )

        self.authenticate(self.owner)

        response = self.client.patch(
            f"/api/events/manage/{event.id}/",
            {"description": "Updated description"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        event.refresh_from_db()

        self.assertEqual(event.status, Event.Status.DRAFT)
        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.PENDING,
        )
        self.assertEqual(event.reviewed_by, self.staff)
        self.assertIsNotNone(event.reviewed_at)
        self.assertEqual(event.review_notes, "Please correct the event details.")
        self.assertEqual(event.moderation_history.count(), 1)

    def test_edit_then_reapprove_keeps_both_moderation_decisions(self):
        event = self.create_event(
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.APPROVED,
            reviewed_by=self.staff,
            reviewed_at=timezone.now(),
            review_notes="First approval",
        )
        EventModerationReview.objects.create(
            event=event,
            reviewer=self.staff,
            decision=EventModerationReview.Decision.APPROVED,
            review_notes="First approval",
        )

        self.authenticate(self.owner)
        update_response = self.client.patch(
            f"/api/events/manage/{event.id}/",
            {"title": "Revised event"},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.data["moderation_status"], "pending")
        self.assertEqual(len(update_response.data["moderation_history"]), 1)

        self.authenticate(self.staff)
        review_response = self.client.post(
            f"/api/events/moderation/{event.id}/review/",
            {"decision": "approve", "review_notes": "Updated details checked."},
            format="json",
        )
        self.assertEqual(review_response.status_code, 200)
        event.refresh_from_db()
        self.assertEqual(event.moderation_status, Event.ModerationStatus.APPROVED)
        self.assertEqual(event.moderation_history.count(), 2)

    def test_hub_manager_cannot_publish_event_through_update_api(self):
        event = self.create_event(
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )
        self.authenticate(self.owner)

        response = self.client.patch(
            f"/api/events/manage/{event.id}/",
            {
                "title": "Attempt to bypass moderation",
                "status": Event.Status.PUBLISHED,
                "moderation_status": Event.ModerationStatus.APPROVED,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.DRAFT)
        self.assertEqual(event.moderation_status, Event.ModerationStatus.PENDING)

    def test_editing_pending_event_keeps_it_pending(self):
        event = self.create_event(
            status=Event.Status.DRAFT,
            moderation_status=Event.ModerationStatus.PENDING,
        )

        self.authenticate(self.owner)

        response = self.client.patch(
            f"/api/events/manage/{event.id}/",
            {"title": "Updated Pending Event"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        event.refresh_from_db()

        self.assertEqual(event.status, Event.Status.DRAFT)
        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.PENDING,
        )

    # --------------------------------------------------
    # EVENT CANCELLATION TESTS
    # --------------------------------------------------

    def test_owner_can_cancel_published_event(self):
        event = self.create_event(
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.APPROVED,
        )

        self.authenticate(self.owner)

        response = self.client.post(
            f"/api/events/manage/{event.id}/cancel/"
        )

        self.assertEqual(response.status_code, 200)

        event.refresh_from_db()

        self.assertEqual(event.status, Event.Status.CANCELLED)
        self.assertEqual(
            event.moderation_status,
            Event.ModerationStatus.APPROVED,
        )
        self.assertTrue(Notification.objects.filter(
            recipient=self.editor,
            event=event,
            verb=Notification.Verb.EVENT_CANCELLED,
        ).exists())

    def test_member_cannot_cancel_published_event(self):
        event = self.create_event(
            status=Event.Status.PUBLISHED,
            moderation_status=Event.ModerationStatus.APPROVED,
        )

        self.authenticate(self.member)

        response = self.client.post(
            f"/api/events/manage/{event.id}/cancel/"
        )

        self.assertEqual(response.status_code, 403)

        event.refresh_from_db()

        self.assertEqual(event.status, Event.Status.PUBLISHED)

    def test_cancelled_event_cannot_be_edited(self):
        event = self.create_event(
            status=Event.Status.CANCELLED,
            moderation_status=Event.ModerationStatus.APPROVED,
        )

        self.authenticate(self.owner)

        response = self.client.patch(
            f"/api/events/manage/{event.id}/",
            {"title": "Attempted Update"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_completed_event_cannot_be_edited(self):
        event = self.create_event(
            status=Event.Status.COMPLETED,
            moderation_status=Event.ModerationStatus.APPROVED,
        )

        self.authenticate(self.owner)

        response = self.client.patch(
            f"/api/events/manage/{event.id}/",
            {"title": "Attempted Update"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
