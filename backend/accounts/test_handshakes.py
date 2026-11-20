from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Follow, Handshake, Notification, Profile


User = get_user_model()


class HandshakeAPITests(TestCase):
    def setUp(self):
        self.sender = self.create_user("handshake_sender")
        self.recipient = self.create_user("handshake_recipient")
        self.other = self.create_user("handshake_other")
        self.create_profile(self.sender)
        self.create_profile(self.recipient)
        self.create_profile(self.other)
        self.client = APIClient()
        self.client.force_authenticate(user=self.sender)

    @staticmethod
    def create_user(username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPassword123!",
            email_verified=True,
        )

    @staticmethod
    def create_profile(user, visibility=Profile.Visibility.PUBLIC):
        return Profile.objects.create(
            user=user,
            profile_type=Profile.ProfileType.STUDENT,
            visibility=visibility,
        )

    def send(self, recipient=None):
        return self.client.post(
            "/api/accounts/handshakes/",
            {"recipient_username": (recipient or self.recipient).username},
            format="json",
        )

    def test_request_is_separate_from_follow_and_visible_only_to_relevant_users(self):
        sent = self.send()
        self.assertEqual(sent.status_code, 201)
        self.assertEqual(sent.data["state"]["state"], "outgoing_pending")
        handshake_id = sent.data["handshake"]["id"]
        handshake = Handshake.objects.get(pk=handshake_id)

        self.assertEqual(handshake.status, Handshake.Status.PENDING)
        self.assertFalse(Follow.objects.exists())
        self.assertEqual(Notification.objects.filter(
            recipient=self.recipient,
            actor=self.sender,
            verb=Notification.Verb.HANDSHAKE_REQUEST,
            handshake=handshake,
        ).count(), 1)

        self.assertEqual(self.client.get("/api/accounts/handshakes/outgoing/").data["count"], 1)
        self.client.force_authenticate(user=self.recipient)
        self.assertEqual(self.client.get("/api/accounts/handshakes/incoming/").data["count"], 1)
        status_view = self.client.get(
            f"/api/accounts/handshakes/status/{self.sender.username}/"
        )
        self.assertEqual(status_view.data["state"], "incoming_pending")
        notification = self.client.get("/api/accounts/notifications/").data["results"][0]
        self.assertEqual(notification["verb"], Notification.Verb.HANDSHAKE_REQUEST)
        self.assertEqual(notification["handshake_id"], str(handshake.pk))
        self.assertEqual(notification["handshake_status"], Handshake.Status.PENDING)
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get("/api/accounts/handshakes/incoming/").data["count"], 0)
        self.assertEqual(self.client.get("/api/accounts/handshakes/outgoing/").data["count"], 0)
        self.assertEqual(self.client.get("/api/accounts/handshakes/connections/").data["count"], 0)

    def test_duplicate_and_reverse_pending_requests_do_not_create_duplicates(self):
        first = self.send()
        repeated = self.send()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(Handshake.objects.count(), 1)
        self.assertEqual(Notification.objects.filter(verb=Notification.Verb.HANDSHAKE_REQUEST).count(), 1)

        self.client.force_authenticate(user=self.recipient)
        reverse = self.send(self.sender)
        self.assertEqual(reverse.status_code, 200)
        self.assertEqual(reverse.data["state"]["state"], "incoming_pending")
        self.assertEqual(Handshake.objects.count(), 1)

    def test_self_private_and_invalid_request_inputs_are_rejected(self):
        self_request = self.send(self.sender)
        private = self.create_user("handshake_private")
        self.create_profile(private, Profile.Visibility.PRIVATE)
        private_request = self.send(private)
        invalid = self.client.post(
            "/api/accounts/handshakes/",
            {"recipient_username": self.other.username, "status": "accepted"},
            format="json",
        )
        self.assertEqual(self_request.status_code, 400)
        self.assertEqual(private_request.status_code, 404)
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(Handshake.objects.count(), 0)

    def test_handshake_lists_and_actions_require_authentication(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/accounts/handshakes/incoming/").status_code, 401)
        self.assertEqual(self.client.get("/api/accounts/handshakes/outgoing/").status_code, 401)
        self.assertEqual(self.client.get("/api/accounts/handshakes/connections/").status_code, 401)
        self.assertEqual(self.client.post(
            "/api/accounts/handshakes/",
            {"recipient_username": self.recipient.username},
            format="json",
        ).status_code, 401)

    def test_recipient_can_accept_and_both_users_see_connection(self):
        response = self.send()
        handshake_id = response.data["handshake"]["id"]
        self.client.force_authenticate(user=self.recipient)
        accepted = self.client.post(
            f"/api/accounts/handshakes/requests/{handshake_id}/accept/",
        )

        self.assertEqual(accepted.status_code, 200)
        handshake = Handshake.objects.get(pk=handshake_id)
        self.assertEqual(handshake.status, Handshake.Status.ACCEPTED)
        self.assertEqual(handshake.responded_by, self.recipient)
        self.assertIsNotNone(handshake.responded_at)
        self.assertEqual(self.client.get("/api/accounts/handshakes/connections/").data["count"], 1)

        request_notice = Notification.objects.get(verb=Notification.Verb.HANDSHAKE_REQUEST)
        request_notice.refresh_from_db()
        self.assertIsNotNone(request_notice.read_at)
        accepted_notice = Notification.objects.get(verb=Notification.Verb.HANDSHAKE_ACCEPTED)
        self.assertEqual(accepted_notice.recipient, self.sender)
        self.assertEqual(accepted_notice.handshake, handshake)

        self.client.force_authenticate(user=self.sender)
        self.assertEqual(self.client.get("/api/accounts/handshakes/connections/").data["count"], 1)
        duplicate = self.send(self.recipient)
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(Handshake.objects.filter(status=Handshake.Status.ACCEPTED).count(), 1)

    def test_only_recipient_can_accept_or_reject_and_transitions_are_final(self):
        response = self.send()
        handshake_id = response.data["handshake"]["id"]
        wrong_user = self.client.post(
            f"/api/accounts/handshakes/requests/{handshake_id}/accept/",
        )
        self.assertEqual(wrong_user.status_code, 403)

        self.client.force_authenticate(user=self.recipient)
        rejected = self.client.post(
            f"/api/accounts/handshakes/requests/{handshake_id}/reject/",
        )
        accept_after_reject = self.client.post(
            f"/api/accounts/handshakes/requests/{handshake_id}/accept/",
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(accept_after_reject.status_code, 400)
        handshake = Handshake.objects.get(pk=handshake_id)
        self.assertEqual(handshake.status, Handshake.Status.REJECTED)
        self.assertEqual(handshake.responded_by, self.recipient)
        self.assertFalse(Notification.objects.filter(verb=Notification.Verb.HANDSHAKE_ACCEPTED).exists())
        request_notice = Notification.objects.get(verb=Notification.Verb.HANDSHAKE_REQUEST)
        request_notice.refresh_from_db()
        self.assertIsNotNone(request_notice.read_at)
        self.assertEqual(request_notice.handshake.status, Handshake.Status.REJECTED)
        self.client.force_authenticate(user=self.sender)
        again = self.send()
        self.assertEqual(again.status_code, 201)
        self.assertEqual(Handshake.objects.filter(
            requester=self.sender,
            recipient=self.recipient,
        ).count(), 2)

    def test_only_sender_can_cancel_pending_request(self):
        response = self.send()
        handshake_id = response.data["handshake"]["id"]
        self.client.force_authenticate(user=self.recipient)
        denied = self.client.post(
            f"/api/accounts/handshakes/requests/{handshake_id}/cancel/",
        )
        self.assertEqual(denied.status_code, 403)

        self.client.force_authenticate(user=self.sender)
        cancelled = self.client.post(
            f"/api/accounts/handshakes/requests/{handshake_id}/cancel/",
        )
        self.assertEqual(cancelled.status_code, 200)
        handshake = Handshake.objects.get(pk=handshake_id)
        self.assertEqual(handshake.status, Handshake.Status.CANCELLED)
        self.assertEqual(handshake.cancelled_by, self.sender)
        self.assertIsNotNone(handshake.cancelled_at)
        notice = Notification.objects.get(verb=Notification.Verb.HANDSHAKE_REQUEST)
        notice.refresh_from_db()
        self.assertIsNone(notice.read_at)
        self.assertEqual(notice.handshake.status, Handshake.Status.CANCELLED)

    def test_either_connection_owner_can_remove_an_accepted_connection(self):
        response = self.send()
        handshake_id = response.data["handshake"]["id"]
        self.client.force_authenticate(user=self.recipient)
        self.client.post(f"/api/accounts/handshakes/requests/{handshake_id}/accept/")
        self.client.force_authenticate(user=self.other)
        denied = self.client.delete(f"/api/accounts/handshakes/connections/{handshake_id}/")
        self.assertEqual(denied.status_code, 403)

        self.client.force_authenticate(user=self.recipient)
        removed = self.client.delete(f"/api/accounts/handshakes/connections/{handshake_id}/")
        self.assertEqual(removed.status_code, 200)
        handshake = Handshake.objects.get(pk=handshake_id)
        self.assertEqual(handshake.status, Handshake.Status.CANCELLED)
        self.assertEqual(handshake.cancelled_by, self.recipient)
        self.assertEqual(self.client.get("/api/accounts/handshakes/connections/").data["count"], 0)


    def test_database_constraint_blocks_duplicate_accepted_pair(self):
        response = self.send()
        handshake = Handshake.objects.get(pk=response.data["handshake"]["id"])
        self.client.force_authenticate(user=self.recipient)
        self.client.post(f"/api/accounts/handshakes/requests/{handshake.id}/accept/")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Handshake.objects.create(
                    requester=self.recipient,
                    recipient=self.sender,
                    status=Handshake.Status.ACCEPTED,
                )
