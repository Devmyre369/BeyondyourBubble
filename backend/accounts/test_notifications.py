from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Notification, Profile, User


class NotificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.actor = User.objects.create_user(
            username="actor",
            email="actor@example.com",
            password="TestPassword123!",
            email_verified=True,
        )
        self.recipient = User.objects.create_user(
            username="recipient",
            email="recipient@example.com",
            password="TestPassword123!",
            email_verified=True,
        )
        Profile.objects.create(
            user=self.actor,
            profile_type=Profile.ProfileType.STUDENT,
        )
        Profile.objects.create(
            user=self.recipient,
            profile_type=Profile.ProfileType.STUDENT,
        )

    def test_follow_creates_one_notification_for_target(self):
        self.client.force_authenticate(user=self.actor)
        url = "/api/accounts/profile/recipient/follow/"

        first_response = self.client.post(url)
        second_response = self.client.post(url)

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.recipient,
                actor=self.actor,
                verb=Notification.Verb.FOLLOW,
            ).count(),
            1,
        )

    def test_user_can_list_and_mark_only_their_notifications_read(self):
        notification = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            verb=Notification.Verb.FOLLOW,
        )
        self.client.force_authenticate(user=self.recipient)

        list_response = self.client.get("/api/accounts/notifications/")
        read_response = self.client.post(
            f"/api/accounts/notifications/{notification.id}/read/"
        )
        read_all_response = self.client.post(
            "/api/accounts/notifications/read-all/"
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["unread_count"], 1)
        self.assertEqual(
            list_response.data["results"][0]["actor_username"],
            self.actor.username,
        )
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(read_all_response.data["read_count"], 0)

        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)

    def test_user_cannot_mark_another_users_notification_read(self):
        notification = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            verb=Notification.Verb.FOLLOW,
        )
        self.client.force_authenticate(user=self.actor)

        response = self.client.post(
            f"/api/accounts/notifications/{notification.id}/read/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        notification.refresh_from_db()
        self.assertIsNone(notification.read_at)
