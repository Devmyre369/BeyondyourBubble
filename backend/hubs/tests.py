import uuid as uuid_module
from unittest.mock import patch

from django.test import TestCase
from django.db import IntegrityError

from rest_framework.exceptions import ValidationError, PermissionDenied

from django.contrib.auth import get_user_model

from .models import Hub, HubMembership, HubApplication

User = get_user_model()


class HubModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="hub_creator",
            email="creator@example.com",
            password="TestPassword123!",
        )

    def create_hub(self, **kwargs):
        defaults = {
            "name": "Test Company Hub",
            "slug": "test-company-hub",
            "hub_type": Hub.HubType.COMPANY,
            "short_description": "A test company hub.",
            "description": "Full description of the test company hub.",
            "logo": "https://example.com/logo.png",
            "cover_image": "https://example.com/cover.png",
            "website": "https://example.com",
            "contact_email": "contact@example.com",
            "city": "Lucknow",
            "college_or_parent_organisation": "Test University",
            "created_by": self.user,
            "owner": self.user,
        }
        defaults.update(kwargs)
        return Hub.objects.create(**defaults)

    def test_valid_hub_creation(self):
        hub = self.create_hub()
        self.assertTrue(hub.id)
        self.assertEqual(hub.name, "Test Company Hub")
        self.assertEqual(hub.slug, "test-company-hub")
        self.assertEqual(hub.hub_type, Hub.HubType.COMPANY)
        self.assertEqual(hub.short_description, "A test company hub.")
        self.assertEqual(hub.description, "Full description of the test company hub.")
        self.assertEqual(hub.logo, "https://example.com/logo.png")
        self.assertEqual(hub.cover_image, "https://example.com/cover.png")
        self.assertEqual(hub.website, "https://example.com")
        self.assertEqual(hub.contact_email, "contact@example.com")
        self.assertEqual(hub.city, "Lucknow")
        self.assertEqual(
            hub.college_or_parent_organisation, "Test University"
        )
        self.assertEqual(hub.created_by, self.user)
        self.assertEqual(hub.owner, self.user)
        self.assertFalse(hub.is_verified)
        self.assertTrue(hub.is_active)
        self.assertIsNotNone(hub.created_at)
        self.assertIsNotNone(hub.updated_at)

    def test_all_supported_hub_types(self):
        for hub_type, _ in Hub.HubType.choices:
            hub = self.create_hub(
                slug=f"hub-{hub_type}",
                hub_type=hub_type,
            )
            self.assertEqual(hub.hub_type, hub_type)

    def test_slug_must_be_unique(self):
        self.create_hub(slug="unique-slug")
        with self.assertRaises(IntegrityError):
            self.create_hub(slug="unique-slug")

    def test_default_is_verified_false(self):
        hub = self.create_hub()
        self.assertFalse(hub.is_verified)

    def test_default_is_active_true(self):
        hub = self.create_hub()
        self.assertTrue(hub.is_active)

    def test_hub_str(self):
        hub = self.create_hub()
        self.assertEqual(str(hub), "Test Company Hub")

    def test_uuid_primary_key(self):
        hub = self.create_hub()
        uuid_module.UUID(str(hub.id))

    def test_foreign_key_created_by(self):
        hub = self.create_hub()
        self.assertIn(hub, self.user.created_hubs.all())

    def test_foreign_key_owner(self):
        hub = self.create_hub()
        self.assertIn(hub, self.user.owned_hubs.all())


class HubMembershipModelTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="hub_owner",
            email="owner@example.com",
            password="TestPassword123!",
        )
        self.user = User.objects.create_user(
            username="member_user",
            email="member@example.com",
            password="TestPassword123!",
        )
        self.hub = Hub.objects.create(
            name="Test Hub",
            slug="test-hub",
            hub_type=Hub.HubType.ORGANISATION,
            created_by=self.owner,
            owner=self.owner,
        )

    def create_membership(self, **kwargs):
        defaults = {
            "hub": self.hub,
            "user": self.user,
            "role": HubMembership.Role.MEMBER,
            "status": HubMembership.Status.APPROVED,
        }
        defaults.update(kwargs)
        return HubMembership.objects.create(**defaults)

    def test_valid_membership_creation(self):
        membership = self.create_membership()
        self.assertTrue(membership.id)
        self.assertEqual(membership.hub, self.hub)
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.role, HubMembership.Role.MEMBER)
        self.assertEqual(membership.status, HubMembership.Status.APPROVED)
        self.assertIsNotNone(membership.created_at)

    def test_all_supported_membership_roles(self):
        for role, _ in HubMembership.Role.choices:
            membership = self.create_membership(
                user=User.objects.create_user(
                    username=f"user_{role}",
                    email=f"role_{role}@example.com",
                    password="TestPassword123!",
                ),
                role=role,
            )
            self.assertEqual(membership.role, role)

    def test_all_supported_membership_statuses(self):
        for status, _ in HubMembership.Status.choices:
            membership = self.create_membership(
                user=User.objects.create_user(
                    username=f"user_{status}",
                    email=f"status_{status}@example.com",
                    password="TestPassword123!",
                ),
                status=status,
            )
            self.assertEqual(membership.status, status)

    def test_duplicate_membership_prevention(self):
        HubMembership.objects.create(
            hub=self.hub,
            user=self.user,
            role=HubMembership.Role.MEMBER,
            status=HubMembership.Status.APPROVED,
        )
        with self.assertRaises(IntegrityError):
            HubMembership.objects.create(
                hub=self.hub,
                user=self.user,
                role=HubMembership.Role.ADMIN,
                status=HubMembership.Status.PENDING,
            )

    def test_default_status_is_pending(self):
        membership = HubMembership.objects.create(
            hub=self.hub,
            user=self.user,
            role=HubMembership.Role.MEMBER,
        )
        self.assertEqual(membership.status, HubMembership.Status.PENDING)

    def test_default_role_is_member(self):
        membership = HubMembership.objects.create(
            hub=self.hub,
            user=self.user,
            status=HubMembership.Status.APPROVED,
        )
        self.assertEqual(membership.role, HubMembership.Role.MEMBER)

    def test_foreign_key_relationships(self):
        membership = self.create_membership()
        self.assertIn(membership, self.hub.memberships.all())
        self.assertIn(membership, self.user.hub_memberships.all())

    def test_uuid_primary_key(self):
        membership = self.create_membership()
        uuid_module.UUID(str(membership.id))

    def test_membership_str(self):
        membership = self.create_membership()
        expected = f"{self.user.username} - {self.hub.name} ({membership.role})"
        self.assertEqual(str(membership), expected)


class HubApplicationServiceTests(TestCase):

    def setUp(self):
        self.applicant = User.objects.create_user(
            username="applicant",
            email="applicant@example.com",
            password="TestPassword123!",
        )
        self.staff = User.objects.create_user(
            username="staff_user",
            email="staff@example.com",
            password="TestPassword123!",
            is_staff=True,
        )
        self.ordinary_user = User.objects.create_user(
            username="ordinary_user",
            email="ordinary@example.com",
            password="TestPassword123!",
        )

    def create_application(self, **kwargs):
        defaults = {
            "applicant": self.applicant,
            "requested_name": "Test Company Hub",
            "requested_slug": "test-company-hub",
            "hub_type": Hub.HubType.COMPANY,
            "organisation_description": "A test company.",
            "college_or_parent_organisation": "Test University",
            "city": "Lucknow",
            "website": "https://example.com",
            "contact_email": "contact@example.com",
            "status": HubApplication.Status.PENDING,
        }
        defaults.update(kwargs)
        return HubApplication.objects.create(**defaults)

    def test_application_submission(self):
        application = self.create_application()
        self.assertTrue(application.id)
        self.assertEqual(application.applicant, self.applicant)
        self.assertEqual(application.requested_name, "Test Company Hub")
        self.assertEqual(application.requested_slug, "test-company-hub")
        self.assertEqual(application.hub_type, Hub.HubType.COMPANY)
        self.assertEqual(
            application.organisation_description, "A test company."
        )
        self.assertEqual(
            application.college_or_parent_organisation, "Test University"
        )
        self.assertEqual(application.city, "Lucknow")
        self.assertEqual(application.website, "https://example.com")
        self.assertEqual(application.contact_email, "contact@example.com")
        self.assertEqual(application.status, HubApplication.Status.PENDING)
        self.assertIsNone(application.reviewer)
        self.assertIsNone(application.reviewed_at)
        self.assertIsNotNone(application.created_at)

    def test_all_supported_hub_types(self):
        for hub_type, _ in Hub.HubType.choices:
            application = self.create_application(
                requested_slug=f"hub-{hub_type}",
                hub_type=hub_type,
            )
            self.assertEqual(application.hub_type, hub_type)

    def test_invalid_application_data_rejected(self):
        from hubs.services.application_service import submit_application

        with self.assertRaises(ValidationError):
            submit_application(
                self.applicant,
                {
                    "requested_name": "Test Company Hub",
                    "requested_slug": "",
                    "hub_type": Hub.HubType.COMPANY,
                },
            )

    def test_submission_service_prevents_duplicate_pending(self):
        from hubs.services.application_service import submit_application

        submit_application(
            self.applicant,
            {
                "requested_name": "Test Company Hub",
                "requested_slug": "test-company-hub",
                "hub_type": Hub.HubType.COMPANY,
            },
        )

        with self.assertRaises(ValidationError):
            submit_application(
                self.applicant,
                {
                    "requested_name": "Test Company Hub",
                    "requested_slug": "test-company-hub",
                    "hub_type": Hub.HubType.COMPANY,
                },
            )

    def test_submission_service_allows_rejected_reapply(self):
        from hubs.services.application_service import submit_application

        submit_application(
            self.applicant,
            {
                "requested_name": "Test Company Hub",
                "requested_slug": "test-company-hub",
                "hub_type": Hub.HubType.COMPANY,
            },
        )

        application = HubApplication.objects.get(
            applicant=self.applicant,
            requested_slug="test-company-hub",
        )
        application.status = HubApplication.Status.REJECTED
        application.save()

        # A new pending application for the same slug should now be allowed.
        submit_application(
            self.applicant,
            {
                "requested_name": "Test Company Hub Again",
                "requested_slug": "test-company-hub",
                "hub_type": Hub.HubType.COMPANY,
            },
        )

        self.assertEqual(
            HubApplication.objects.filter(
                applicant=self.applicant,
                requested_slug="test-company-hub",
                status=HubApplication.Status.PENDING,
            ).count(),
            1,
        )

    def test_approval_creates_exactly_one_hub(self):
        from hubs.services.application_service import approve_application

        application = self.create_application()

        result = approve_application(application, self.staff)

        self.assertTrue(result["created"])
        self.assertIsNotNone(result["hub"])
        self.assertEqual(result["hub"].name, "Test Company Hub")
        self.assertEqual(result["hub"].slug, "test-company-hub")
        self.assertEqual(result["hub"].hub_type, Hub.HubType.COMPANY)
        self.assertEqual(result["hub"].created_by, self.applicant)
        self.assertEqual(result["hub"].owner, self.applicant)
        self.assertFalse(result["hub"].is_verified)
        self.assertTrue(result["hub"].is_active)

        application.refresh_from_db()
        self.assertEqual(application.status, HubApplication.Status.APPROVED)
        self.assertEqual(application.reviewer, self.staff)
        self.assertIsNotNone(application.reviewed_at)

    def test_approval_creates_owner_membership(self):
        from hubs.services.application_service import approve_application

        application = self.create_application()
        approve_application(application, self.staff)

        hub = Hub.objects.get(slug="test-company-hub")
        membership = HubMembership.objects.get(hub=hub, user=self.applicant)

        self.assertEqual(membership.role, HubMembership.Role.OWNER)
        self.assertEqual(membership.status, HubMembership.Status.APPROVED)
        self.assertIsNotNone(membership.joined_at)

    def test_applicant_becomes_owner_and_creator(self):
        from hubs.services.application_service import approve_application

        application = self.create_application()
        approve_application(application, self.staff)

        hub = Hub.objects.get(slug="test-company-hub")

        self.assertEqual(hub.created_by, self.applicant)
        self.assertEqual(hub.owner, self.applicant)
        self.assertIn(hub, self.applicant.created_hubs.all())
        self.assertIn(hub, self.applicant.owned_hubs.all())

        membership = HubMembership.objects.get(hub=hub, user=self.applicant)
        self.assertEqual(membership.role, HubMembership.Role.OWNER)

    def test_rejected_application_creates_no_hub(self):
        from hubs.services.application_service import reject_application

        application = self.create_application()

        result = reject_application(
            application, self.staff, review_notes="Not eligible."
        )

        self.assertFalse(result["created"])
        self.assertIsNone(result["hub"])
        self.assertEqual(
            Hub.objects.filter(slug="test-company-hub").count(), 0
        )
        self.assertEqual(
            HubMembership.objects.filter(hub__slug="test-company-hub").count(),
            0,
        )

        application.refresh_from_db()
        self.assertEqual(application.status, HubApplication.Status.REJECTED)
        self.assertEqual(application.reviewer, self.staff)
        self.assertEqual(application.review_notes, "Not eligible.")
        self.assertIsNotNone(application.reviewed_at)

    def test_duplicate_approval_is_prevented(self):
        from hubs.services.application_service import approve_application

        application = self.create_application()
        approve_application(application, self.staff)

        application.refresh_from_db()
        self.assertEqual(application.status, HubApplication.Status.APPROVED)

        with self.assertRaises(ValidationError):
            approve_application(application, self.staff)

        # Exactly one Hub exists.
        self.assertEqual(
            Hub.objects.filter(slug="test-company-hub").count(), 1
        )

    def test_repeated_rejection_is_prevented(self):
        from hubs.services.application_service import reject_application

        application = self.create_application()
        reject_application(application, self.staff, review_notes="First.")

        application.refresh_from_db()
        self.assertEqual(application.status, HubApplication.Status.REJECTED)

        with self.assertRaises(ValidationError):
            reject_application(application, self.staff, review_notes="Second.")

    def test_approval_rolls_back_on_failure(self):
        from hubs.services.application_service import approve_application
        from unittest.mock import patch

        application = self.create_application()

        with patch.object(
            Hub.objects, "create", side_effect=Exception("boom")
        ):
            with self.assertRaises(Exception):
                approve_application(application, self.staff)

        application.refresh_from_db()
        self.assertEqual(application.status, HubApplication.Status.PENDING)
        self.assertEqual(Hub.objects.count(), 0)
        self.assertEqual(HubMembership.objects.count(), 0)

    def test_reviewer_and_timestamps_recorded(self):
        from hubs.services.application_service import (
            approve_application,
            reject_application,
        )

        application = self.create_application()
        approve_application(application, self.staff)

        application.refresh_from_db()
        self.assertEqual(application.reviewer, self.staff)
        self.assertIsNotNone(application.reviewed_at)
        self.assertEqual(application.status, HubApplication.Status.APPROVED)

    def test_ordinary_user_cannot_approve(self):
        from hubs.services.application_service import approve_application

        application = self.create_application()

        with self.assertRaises(PermissionDenied):
            approve_application(application, self.ordinary_user)

        application.refresh_from_db()
        self.assertEqual(application.status, HubApplication.Status.PENDING)

    def test_applicant_cannot_approve_own_application(self):
        from hubs.services.application_service import approve_application

        # Applicant is also a staff member in this scenario.
        staff_applicant = User.objects.create_user(
            username="staff_applicant",
            email="staff_applicant@example.com",
            password="TestPassword123!",
            is_staff=True,
        )

        application = self.create_application(applicant=staff_applicant)

        with self.assertRaises(PermissionDenied):
            approve_application(application, staff_applicant)

        application.refresh_from_db()
        self.assertEqual(application.status, HubApplication.Status.PENDING)

    def test_only_pending_can_be_approved(self):
        from hubs.services.application_service import approve_application

        application = self.create_application(
            status=HubApplication.Status.APPROVED
        )

        with self.assertRaises(ValidationError):
            approve_application(application, self.staff)

    def test_only_pending_can_be_rejected(self):
        from hubs.services.application_service import reject_application

        application = self.create_application(
            status=HubApplication.Status.REJECTED
        )

        with self.assertRaises(ValidationError):
            reject_application(application, self.staff)

    def test_application_str(self):
        application = self.create_application()
        expected = (
            f"{self.applicant.username} - Test Company Hub ({application.status})"
        )
        self.assertEqual(str(application), expected)

    def test_uuid_primary_key(self):
        application = self.create_application()
        uuid_module.UUID(str(application.id))

