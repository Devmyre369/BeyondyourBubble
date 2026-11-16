import uuid as uuid_module
from unittest.mock import patch

from django.db import IntegrityError, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from accounts.models import Profile

from .models import Hub, HubMembership, HubApplication
from .serializers import HubDetailSerializer

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
        self.assertEqual(
            {hub_type for hub_type, _ in Hub.HubType.choices},
            {
                "college",
                "college_club",
                "college_department",
                "organisation",
                "company",
                "community",
            },
        )

        for hub_type, _ in Hub.HubType.choices:
            hub = self.create_hub(
                slug=f"hub-{hub_type}",
                hub_type=hub_type,
            )
            self.assertEqual(hub.hub_type, hub_type)

    def test_all_supported_visibility_values(self):
        self.assertEqual(
            {visibility for visibility, _ in Hub.Visibility.choices},
            {"public"},
        )

        hub = self.create_hub(
            slug="hub-visibility-public",
            visibility=Hub.Visibility.PUBLIC,
        )
        self.assertEqual(hub.visibility, Hub.Visibility.PUBLIC)

    def test_all_supported_membership_policies(self):
        for policy, _ in Hub.MembershipPolicy.choices:
            hub = self.create_hub(
                slug=f"hub-membership-{policy.replace('_', '-')}",
                membership_policy=policy,
            )
            self.assertEqual(hub.membership_policy, policy)

    def test_safe_policy_defaults(self):
        hub = self.create_hub()
        self.assertEqual(hub.visibility, Hub.Visibility.PUBLIC)
        self.assertEqual(
            hub.membership_policy,
            Hub.MembershipPolicy.APPROVAL_REQUIRED,
        )

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
        self.assertEqual(
            result["hub"].visibility,
            Hub.Visibility.PUBLIC,
        )
        self.assertEqual(
            result["hub"].membership_policy,
            Hub.MembershipPolicy.APPROVAL_REQUIRED,
        )

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


class HubVisibilityMigrationTests(TransactionTestCase):
    migrate_from = [("hubs", "0003_add_hub_policies")]
    migrate_to = [("hubs", "0004_public_hub_visibility")]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)

        old_apps = executor.loader.project_state(self.migrate_from).apps
        Hub = old_apps.get_model("hubs", "Hub")

        user = User.objects.create(
            username="visibility-migration-user",
            email="visibility-migration@example.com",
            onboarding_completed=False,
        )
        self.hub_ids = [
            Hub.objects.create(
                name=f"Existing Hub {index}",
                slug=f"existing-visibility-hub-{index}",
                hub_type="company",
                visibility="private",
                membership_policy="approval_required",
                created_by_id=user.pk,
                owner_id=user.pk,
            ).pk
            for index in range(2)
        ]

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_hubs_are_migrated_to_public(self):
        Hub = self.apps.get_model("hubs", "Hub")
        hubs = Hub.objects.filter(pk__in=self.hub_ids)

        self.assertEqual(hubs.count(), 2)
        self.assertEqual(
            set(hubs.values_list("visibility", flat=True)),
            {"public"},
        )
        self.assertEqual(
            set(hubs.values_list("membership_policy", flat=True)),
            {"approval_required"},
        )


class HubDiscoveryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="hub_api_user",
            email="hub_api_user@example.com",
            password="TestPassword123!",
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )
        self.hub_counter = 0

    def create_hub(self, **overrides):
        self.hub_counter += 1
        defaults = {
            "name": f"Test Hub {self.hub_counter}",
            "slug": f"test-hub-{self.hub_counter}",
            "hub_type": Hub.HubType.COMPANY,
            "short_description": "",
            "description": "",
            "logo": "",
            "cover_image": "",
            "website": "",
            "city": "Lucknow",
            "college_or_parent_organisation": "",
            "contact_email": "",
            "created_by": self.user,
            "owner": self.user,
        }
        defaults.update(overrides)
        return Hub.objects.create(**defaults)

    def test_discovery_requires_authentication(self):
        self.client.credentials()

        response = self.client.get("/api/hubs/")

        self.assertEqual(response.status_code, 401)

    def test_detail_requires_authentication(self):
        hub = self.create_hub()
        self.client.credentials()

        response = self.client.get(f"/api/hubs/{hub.id}/")

        self.assertEqual(response.status_code, 401)

    def test_create_requires_authentication(self):
        self.client.credentials()

        response = self.client.post(
            "/api/hubs/",
            {
                "name": "Unauthenticated Hub",
                "hub_type": Hub.HubType.COMMUNITY,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Hub.objects.count(), 0)

    def test_create_returns_safe_detail_representation(self):
        response = self.client.post(
            "/api/hubs/",
            {
                "name": "Robotics Society",
                "hub_type": Hub.HubType.COLLEGE_CLUB,
                "description": "A campus robotics community.",
                "contact_email": "private@example.com",
                "city": "Lucknow",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Robotics Society")
        self.assertEqual(response.data["slug"], "robotics-society")
        self.assertEqual(response.data["hub_type"], Hub.HubType.COLLEGE_CLUB)
        self.assertEqual(
            response.data["description"],
            "A campus robotics community.",
        )
        self.assertEqual(response.data["city"], "Lucknow")
        self.assertFalse(response.data["is_verified"])
        self.assertTrue(response.data["created_at"])
        self.assertNotIn("contact_email", response.data)
        self.assertNotIn("owner", response.data)
        self.assertNotIn("created_by", response.data)
        self.assertNotIn("is_active", response.data)

        self.assertEqual(
            set(response.data),
            set(HubDetailSerializer.Meta.fields),
        )

    def test_create_supports_all_hub_categories(self):
        for hub_type, _ in Hub.HubType.choices:
            with self.subTest(hub_type=hub_type):
                response = self.client.post(
                    "/api/hubs/",
                    {
                        "name": f"Hub for {hub_type}",
                        "hub_type": hub_type,
                    },
                    format="json",
                )

                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.data["hub_type"], hub_type)

    def test_create_supports_both_membership_policies_and_default(self):
        for index, policy in enumerate(Hub.MembershipPolicy.values):
            with self.subTest(policy=policy):
                response = self.client.post(
                    "/api/hubs/",
                    {
                        "name": f"Policy Hub {index}",
                        "hub_type": Hub.HubType.COMMUNITY,
                        "membership_policy": policy,
                    },
                    format="json",
                )

                self.assertEqual(response.status_code, 201)
                hub = Hub.objects.get(id=response.data["id"])
                self.assertEqual(hub.membership_policy, policy)

        default_response = self.client.post(
            "/api/hubs/",
            {
                "name": "Default Policy Hub",
                "hub_type": Hub.HubType.COMMUNITY,
            },
            format="json",
        )

        self.assertEqual(default_response.status_code, 201)
        default_hub = Hub.objects.get(id=default_response.data["id"])
        self.assertEqual(
            default_hub.membership_policy,
            Hub.MembershipPolicy.APPROVAL_REQUIRED,
        )

    def test_create_generates_unique_slugs_for_duplicate_names(self):
        first_response = self.client.post(
            "/api/hubs/",
            {"name": "Community Hub", "hub_type": Hub.HubType.COMMUNITY},
            format="json",
        )
        second_response = self.client.post(
            "/api/hubs/",
            {"name": "Community Hub", "hub_type": Hub.HubType.COMMUNITY},
            format="json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)
        self.assertEqual(first_response.data["slug"], "community-hub")
        self.assertEqual(second_response.data["slug"], "community-hub-2")
        self.assertEqual(
            Hub.objects.filter(name="Community Hub").count(),
            2,
        )

    def test_create_assigns_owner_creator_and_approved_owner_membership(self):
        response = self.client.post(
            "/api/hubs/",
            {"name": "Owned Hub", "hub_type": Hub.HubType.ORGANISATION},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        hub = Hub.objects.get(id=response.data["id"])
        self.assertEqual(hub.owner, self.user)
        self.assertEqual(hub.created_by, self.user)

        membership = HubMembership.objects.get(hub=hub, user=self.user)
        self.assertEqual(membership.role, HubMembership.Role.OWNER)
        self.assertEqual(membership.status, HubMembership.Status.APPROVED)
        self.assertIsNotNone(membership.joined_at)

    def test_create_rejects_private_visibility(self):
        response = self.client.post(
            "/api/hubs/",
            {
                "name": "Private Hub",
                "hub_type": Hub.HubType.COMMUNITY,
                "visibility": "private",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("visibility", response.data)
        self.assertEqual(Hub.objects.count(), 0)

    def test_create_ignores_attempts_to_override_protected_fields(self):
        other_user = User.objects.create_user(
            username="hub_attacker",
            email="hub_attacker@example.com",
            password="TestPassword123!",
        )
        response = self.client.post(
            "/api/hubs/",
            {
                "name": "Protected Fields Hub",
                "hub_type": Hub.HubType.COMPANY,
                "slug": "client-chosen-slug",
                "owner": str(other_user.id),
                "created_by": str(other_user.id),
                "is_active": False,
                "is_verified": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        hub = Hub.objects.get(id=response.data["id"])
        self.assertEqual(hub.slug, "protected-fields-hub")
        self.assertEqual(hub.owner, self.user)
        self.assertEqual(hub.created_by, self.user)
        self.assertTrue(hub.is_active)
        self.assertFalse(hub.is_verified)

    def test_create_rejects_missing_and_invalid_fields(self):
        invalid_payloads = [
            ({"hub_type": Hub.HubType.COMMUNITY}, "name"),
            ({"name": "Missing type"}, "hub_type"),
            (
                {"name": "Invalid type", "hub_type": "invalid"},
                "hub_type",
            ),
            (
                {
                    "name": "Invalid policy",
                    "hub_type": Hub.HubType.COMMUNITY,
                    "membership_policy": "invalid",
                },
                "membership_policy",
            ),
            (
                {
                    "name": "Invalid website",
                    "hub_type": Hub.HubType.COMMUNITY,
                    "website": "not-a-url",
                },
                "website",
            ),
            (
                {
                    "name": "Invalid email",
                    "hub_type": Hub.HubType.COMMUNITY,
                    "contact_email": "not-an-email",
                },
                "contact_email",
            ),
            (
                {
                    "name": "Invalid description",
                    "hub_type": Hub.HubType.COMMUNITY,
                    "short_description": "x" * 301,
                },
                "short_description",
            ),
        ]

        for payload, field in invalid_payloads:
            with self.subTest(field=field):
                response = self.client.post(
                    "/api/hubs/",
                    payload,
                    format="json",
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)

        self.assertEqual(Hub.objects.count(), 0)

    def test_create_rolls_back_hub_when_owner_membership_fails(self):
        with patch(
            "hubs.services.hub_creation_service.HubMembership.objects.create",
            side_effect=IntegrityError("membership creation failed"),
        ):
            with self.assertRaises(IntegrityError):
                self.client.post(
                    "/api/hubs/",
                    {
                        "name": "Atomic Hub",
                        "hub_type": Hub.HubType.COMMUNITY,
                    },
                    format="json",
                )

        self.assertFalse(Hub.objects.filter(name="Atomic Hub").exists())

    def test_discovery_returns_active_hubs_only(self):
        active_hub = self.create_hub()
        inactive_hub = self.create_hub(
            name="Inactive Hub",
            slug="inactive-hub",
            is_active=False,
        )

        response = self.client.get("/api/hubs/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [str(active_hub.id)],
        )
        self.assertNotIn(
            str(inactive_hub.id),
            [item["id"] for item in response.data["results"]],
        )

    def test_discovery_filters_by_type_and_city(self):
        matching_hub = self.create_hub(
            name="Lucknow Community",
            slug="lucknow-community",
            hub_type=Hub.HubType.COMMUNITY,
            city="Lucknow",
        )
        self.create_hub(
            name="Company in Lucknow",
            slug="company-in-lucknow",
            hub_type=Hub.HubType.COMPANY,
            city="Lucknow",
        )
        self.create_hub(
            name="Community in Delhi",
            slug="community-in-delhi",
            hub_type=Hub.HubType.COMMUNITY,
            city="Delhi",
        )

        response = self.client.get(
            "/api/hubs/?hub_type=community&city=lucknow"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            str(matching_hub.id),
        )

    def test_discovery_searches_name_and_descriptions(self):
        name_match = self.create_hub(
            name="Robotics Society",
            slug="robotics-society",
        )
        description_match = self.create_hub(
            name="Engineering Hub",
            slug="engineering-hub",
            description="A place for robotics projects.",
        )
        short_description_match = self.create_hub(
            name="Student Makers",
            slug="student-makers",
            short_description="Robotics enthusiasts welcome.",
        )
        self.create_hub(
            name="Art Circle",
            slug="art-circle",
            description="Painting and design.",
        )

        response = self.client.get("/api/hubs/?search=ROBOTICS")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(
            {item["id"] for item in response.data["results"]},
            {
                str(name_match.id),
                str(description_match.id),
                str(short_description_match.id),
            },
        )

    def test_discovery_uses_ten_item_page_number_pagination(self):
        for index in range(11):
            self.create_hub(
                name=f"Paginated Hub {index}",
                slug=f"paginated-hub-{index}",
            )

        first_page = self.client.get("/api/hubs/?page=1")
        second_page = self.client.get("/api/hubs/?page=2")
        beyond_last_page = self.client.get("/api/hubs/?page=3")

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data["count"], 11)
        self.assertEqual(len(first_page.data["results"]), 10)
        self.assertEqual(first_page.data["next"], 2)
        self.assertIsNone(first_page.data["previous"])

        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(len(second_page.data["results"]), 1)
        self.assertIsNone(second_page.data["next"])
        self.assertEqual(second_page.data["previous"], 1)

        self.assertEqual(beyond_last_page.status_code, 200)
        self.assertEqual(beyond_last_page.data["count"], 11)
        self.assertEqual(beyond_last_page.data["results"], [])
        self.assertIsNone(beyond_last_page.data["next"])
        self.assertEqual(beyond_last_page.data["previous"], 2)

    def test_discovery_rejects_invalid_page_values_like_feed(self):
        for page in ("invalid", "0", "-1"):
            with self.subTest(page=page):
                response = self.client.get(f"/api/hubs/?page={page}")

                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    response.data,
                    {"detail": "Invalid page number."},
                )

    def test_invalid_hub_type_returns_bad_request(self):
        response = self.client.get("/api/hubs/?hub_type=invalid")

        self.assertEqual(response.status_code, 400)
        self.assertIn("hub_type", response.data)

    def test_detail_returns_public_fields_without_internal_fields(self):
        hub = self.create_hub(
            name="Detail Hub",
            slug="detail-hub",
            short_description="A short description.",
            description="A full description.",
            logo="https://example.com/logo.png",
            cover_image="https://example.com/cover.png",
            website="https://example.com",
            city="Lucknow",
            college_or_parent_organisation="BYB University",
            contact_email="private@example.com",
            is_verified=True,
        )

        response = self.client.get(f"/api/hubs/{hub.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(hub.id))
        self.assertEqual(response.data["name"], "Detail Hub")
        self.assertEqual(response.data["slug"], "detail-hub")
        self.assertEqual(response.data["hub_type"], Hub.HubType.COMPANY)
        self.assertEqual(response.data["short_description"], "A short description.")
        self.assertEqual(response.data["description"], "A full description.")
        self.assertEqual(response.data["logo"], "https://example.com/logo.png")
        self.assertEqual(response.data["cover_image"], "https://example.com/cover.png")
        self.assertEqual(response.data["website"], "https://example.com")
        self.assertEqual(response.data["city"], "Lucknow")
        self.assertEqual(
            response.data["college_or_parent_organisation"],
            "BYB University",
        )
        self.assertTrue(response.data["is_verified"])
        self.assertTrue(response.data["created_at"])
        self.assertNotIn("contact_email", response.data)
        self.assertNotIn("owner", response.data)
        self.assertNotIn("created_by", response.data)

    def test_detail_returns_not_found_for_inactive_hub(self):
        hub = self.create_hub(
            name="Inactive Detail Hub",
            slug="inactive-detail-hub",
            is_active=False,
        )

        response = self.client.get(f"/api/hubs/{hub.id}/")

        self.assertEqual(response.status_code, 404)

    def test_detail_returns_not_found_for_nonexistent_hub(self):
        response = self.client.get(
            "/api/hubs/00000000-0000-0000-0000-000000000000/"
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_update_profile_fields_without_changing_identity(self):
        hub = self.create_hub()
        owner_membership = HubMembership.objects.create(
            hub=hub,
            user=self.user,
            role=HubMembership.Role.OWNER,
            status=HubMembership.Status.APPROVED,
        )
        member = User.objects.create_user(
            username="update_member",
            email="update_member@example.com",
            password="TestPassword123!",
        )
        member_membership = HubMembership.objects.create(
            hub=hub,
            user=member,
            role=HubMembership.Role.MEMBER,
            status=HubMembership.Status.APPROVED,
        )
        hub_id = hub.id
        hub_slug = hub.slug

        response = self.client.patch(
            f"/api/hubs/{hub.id}/",
            {
                "name": "Updated Hub",
                "hub_type": Hub.HubType.COLLEGE,
                "short_description": "Updated short description.",
                "description": "Updated full description.",
                "logo": "https://example.com/updated-logo.png",
                "cover_image": "https://example.com/updated-cover.png",
                "website": "https://updated.example.com",
                "city": "Delhi",
                "college_or_parent_organisation": "Updated University",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        hub.refresh_from_db()
        self.assertEqual(hub.name, "Updated Hub")
        self.assertEqual(hub.hub_type, Hub.HubType.COLLEGE)
        self.assertEqual(hub.short_description, "Updated short description.")
        self.assertEqual(hub.description, "Updated full description.")
        self.assertEqual(hub.logo, "https://example.com/updated-logo.png")
        self.assertEqual(hub.cover_image, "https://example.com/updated-cover.png")
        self.assertEqual(hub.website, "https://updated.example.com")
        self.assertEqual(hub.city, "Delhi")
        self.assertEqual(
            hub.college_or_parent_organisation,
            "Updated University",
        )
        self.assertEqual(hub.id, hub_id)
        self.assertEqual(hub.slug, hub_slug)
        self.assertEqual(hub.owner, self.user)
        self.assertEqual(hub.created_by, self.user)
        self.assertEqual(
            list(
                hub.memberships.order_by("user_id").values_list(
                    "user_id", "role", "status"
                )
            ),
            sorted([
                (owner_membership.user_id, owner_membership.role, owner_membership.status),
                (member_membership.user_id, member_membership.role, member_membership.status),
            ]),
        )
        self.assertEqual(response.data["id"], str(hub_id))
        self.assertEqual(response.data["slug"], hub_slug)
        self.assertTrue(response.data["can_edit"])
        self.assertTrue(response.data["can_edit_membership_policy"])

    def test_approved_admin_can_update_profile_fields(self):
        hub = self.create_hub()
        admin = User.objects.create_user(
            username="hub_admin",
            email="hub_admin@example.com",
            password="TestPassword123!",
        )
        HubMembership.objects.create(
            hub=hub,
            user=admin,
            role=HubMembership.Role.ADMIN,
            status=HubMembership.Status.APPROVED,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {RefreshToken.for_user(admin).access_token}"
            )
        )

        response = self.client.patch(
            f"/api/hubs/{hub.id}/",
            {"name": "Admin Updated Hub"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        hub.refresh_from_db()
        self.assertEqual(hub.name, "Admin Updated Hub")
        self.assertTrue(response.data["can_edit"])
        self.assertFalse(response.data["can_edit_membership_policy"])

    def test_only_owner_can_change_membership_policy(self):
        hub = self.create_hub()
        admin = User.objects.create_user(
            username="policy_admin",
            email="policy_admin@example.com",
            password="TestPassword123!",
        )
        HubMembership.objects.create(
            hub=hub,
            user=admin,
            role=HubMembership.Role.ADMIN,
            status=HubMembership.Status.APPROVED,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {RefreshToken.for_user(admin).access_token}"
            )
        )

        admin_response = self.client.patch(
            f"/api/hubs/{hub.id}/",
            {"membership_policy": Hub.MembershipPolicy.OPEN},
            format="json",
        )

        self.assertEqual(admin_response.status_code, 403)
        hub.refresh_from_db()
        self.assertEqual(
            hub.membership_policy,
            Hub.MembershipPolicy.APPROVAL_REQUIRED,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {RefreshToken.for_user(self.user).access_token}"
            )
        )
        owner_response = self.client.patch(
            f"/api/hubs/{hub.id}/",
            {"membership_policy": Hub.MembershipPolicy.OPEN},
            format="json",
        )

        self.assertEqual(owner_response.status_code, 200)
        hub.refresh_from_db()
        self.assertEqual(hub.membership_policy, Hub.MembershipPolicy.OPEN)
        self.assertEqual(
            owner_response.data["membership_policy"],
            Hub.MembershipPolicy.OPEN,
        )

    def test_non_editors_cannot_update_hub(self):
        hub = self.create_hub()
        cases = [
            ("editor", HubMembership.Role.EDITOR, HubMembership.Status.APPROVED),
            ("member", HubMembership.Role.MEMBER, HubMembership.Status.APPROVED),
            ("pending_admin", HubMembership.Role.ADMIN, HubMembership.Status.PENDING),
            ("rejected_admin", HubMembership.Role.ADMIN, HubMembership.Status.REJECTED),
        ]

        for suffix, role, membership_status in cases:
            with self.subTest(role=role, status=membership_status):
                user = User.objects.create_user(
                    username=f"not_editor_{suffix}",
                    email=f"not_editor_{suffix}@example.com",
                    password="TestPassword123!",
                )
                HubMembership.objects.create(
                    hub=hub,
                    user=user,
                    role=role,
                    status=membership_status,
                )
                self.client.credentials(
                    HTTP_AUTHORIZATION=(
                        f"Bearer {RefreshToken.for_user(user).access_token}"
                    )
                )
                response = self.client.patch(
                    f"/api/hubs/{hub.id}/",
                    {"name": "Should Not Update"},
                    format="json",
                )

                self.assertEqual(response.status_code, 403)
                hub.refresh_from_db()
                self.assertEqual(hub.name, "Test Hub 1")


    def test_unrelated_and_unauthenticated_users_cannot_update_hub(self):
        hub = self.create_hub()
        unrelated = User.objects.create_user(
            username="unrelated_hub_user",
            email="unrelated_hub_user@example.com",
            password="TestPassword123!",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {RefreshToken.for_user(unrelated).access_token}"
            )
        )
        unrelated_response = self.client.patch(
            f"/api/hubs/{hub.id}/",
            {"name": "Unrelated Update"},
            format="json",
        )
        self.assertEqual(unrelated_response.status_code, 403)

        self.client.credentials()
        unauthenticated_response = self.client.patch(
            f"/api/hubs/{hub.id}/",
            {"name": "Unauthenticated Update"},
            format="json",
        )
        self.assertEqual(unauthenticated_response.status_code, 401)

        hub.refresh_from_db()
        self.assertEqual(hub.name, "Test Hub 1")

    def test_created_by_does_not_grant_edit_permission(self):
        actual_owner = User.objects.create_user(
            username="different_hub_owner",
            email="different_hub_owner@example.com",
            password="TestPassword123!",
        )
        hub = self.create_hub(owner=actual_owner)

        response = self.client.patch(
            f"/api/hubs/{hub.id}/",
            {"name": "Creator Must Not Edit"},
            format="json",
        )
        detail_response = self.client.get(f"/api/hubs/{hub.id}/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(detail_response.status_code, 200)
        self.assertFalse(detail_response.data["can_edit"])
        self.assertFalse(detail_response.data["can_edit_membership_policy"])
        hub.refresh_from_db()
        self.assertEqual(hub.name, "Test Hub 1")

    def test_protected_fields_are_rejected(self):
        hub = self.create_hub()
        other_user = User.objects.create_user(
            username="protected_field_user",
            email="protected_field_user@example.com",
            password="TestPassword123!",
        )
        protected_payload = {
            "id": str(uuid_module.uuid4()),
            "slug": "client-slug",
            "owner": str(other_user.id),
            "created_by": str(other_user.id),
            "visibility": "private",
            "is_verified": True,
            "is_active": False,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "memberships": [],
            "contact_email": "private@example.com",
        }

        response = self.client.patch(
            f"/api/hubs/{hub.id}/",
            protected_payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        for field in protected_payload:
            self.assertIn(field, response.data)
        hub.refresh_from_db()
        self.assertEqual(hub.slug, "test-hub-1")
        self.assertEqual(hub.owner, self.user)
        self.assertEqual(hub.created_by, self.user)
        self.assertEqual(hub.visibility, Hub.Visibility.PUBLIC)
        self.assertFalse(hub.is_verified)
        self.assertTrue(hub.is_active)
        self.assertEqual(hub.memberships.count(), 0)

    def test_detail_capability_flags_match_owner_and_membership_state(self):
        hub = self.create_hub()
        self.assertEqual(
            self.client.get(f"/api/hubs/{hub.id}/").data["can_edit"],
            True,
        )
        self.assertTrue(
            self.client.get(f"/api/hubs/{hub.id}/").data[
                "can_edit_membership_policy"
            ]
        )

        cases = [
            ("approved_admin", HubMembership.Role.ADMIN, HubMembership.Status.APPROVED, True),
            ("pending_admin", HubMembership.Role.ADMIN, HubMembership.Status.PENDING, False),
            ("rejected_admin", HubMembership.Role.ADMIN, HubMembership.Status.REJECTED, False),
            ("editor", HubMembership.Role.EDITOR, HubMembership.Status.APPROVED, False),
            ("member", HubMembership.Role.MEMBER, HubMembership.Status.APPROVED, False),
        ]
        for suffix, role, membership_status, expected_can_edit in cases:
            with self.subTest(role=role, status=membership_status):
                user = User.objects.create_user(
                    username=f"capability_{suffix}",
                    email=f"capability_{suffix}@example.com",
                    password="TestPassword123!",
                )
                HubMembership.objects.create(
                    hub=hub,
                    user=user,
                    role=role,
                    status=membership_status,
                )
                self.client.credentials(
                    HTTP_AUTHORIZATION=(
                        f"Bearer {RefreshToken.for_user(user).access_token}"
                    )
                )
                response = self.client.get(f"/api/hubs/{hub.id}/")

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["can_edit"], expected_can_edit)
                self.assertFalse(response.data["can_edit_membership_policy"])

    def test_update_returns_validation_errors_for_invalid_values(self):
        hub = self.create_hub()
        invalid_payloads = [
            ({"name": ""}, "name"),
            ({"name": "x" * 201}, "name"),
            ({"hub_type": "invalid"}, "hub_type"),
            ({"membership_policy": "invalid"}, "membership_policy"),
            ({"website": "not-a-url"}, "website"),
            ({"logo": "not-a-url"}, "logo"),
            ({"city": "x" * 101}, "city"),
        ]

        for payload, field in invalid_payloads:
            with self.subTest(field=field):
                response = self.client.patch(
                    f"/api/hubs/{hub.id}/",
                    payload,
                    format="json",
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)

        hub.refresh_from_db()
        self.assertEqual(hub.name, "Test Hub 1")


class HubMembershipAPITests(APITestCase):
    def setUp(self):
        self.owner = self.create_user("membership_owner")
        self.user = self.create_user("membership_user")
        self.hub = Hub.objects.create(
            name="Membership Hub",
            slug="membership-hub",
            hub_type=Hub.HubType.COMMUNITY,
            membership_policy=Hub.MembershipPolicy.APPROVAL_REQUIRED,
            created_by=self.owner,
            owner=self.owner,
        )
        self.owner_membership = self.add_membership(
            self.owner,
            role=HubMembership.Role.OWNER,
        )
        self.authenticate_as(self.user)

    def create_user(self, username, **kwargs):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPassword123!",
            email_verified=True,
            **kwargs,
        )

    def authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def add_membership(
        self,
        user,
        *,
        hub=None,
        role=HubMembership.Role.MEMBER,
        membership_status=HubMembership.Status.APPROVED,
    ):
        return HubMembership.objects.create(
            hub=hub or self.hub,
            user=user,
            role=role,
            status=membership_status,
            joined_at=(
                timezone.now()
                if membership_status == HubMembership.Status.APPROVED
                else None
            ),
        )

    def membership_url(self, hub=None):
        return f"/api/hubs/{(hub or self.hub).id}/membership/"

    def members_url(self, hub=None):
        return f"/api/hubs/{(hub or self.hub).id}/members/"

    def requests_url(self, hub=None):
        return f"/api/hubs/{(hub or self.hub).id}/members/requests/"

    def review_url(self, membership, decision, hub=None):
        return (
            f"{self.requests_url(hub)}{membership.id}/{decision}/"
        )

    def test_membership_status_is_personal_and_reports_manager_capabilities(self):
        response = self.client.get(self.membership_url())

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["membership"])
        self.assertEqual(
            response.data["membership_policy"],
            Hub.MembershipPolicy.APPROVAL_REQUIRED,
        )
        self.assertFalse(response.data["can_leave"])
        self.assertFalse(response.data["can_manage_members"])
        self.assertIsNone(response.data["pending_request_count"])

        self.authenticate_as(self.owner)
        owner_response = self.client.get(self.membership_url())
        self.assertEqual(owner_response.status_code, 200)
        self.assertEqual(
            owner_response.data["membership"]["role"],
            HubMembership.Role.OWNER,
        )
        self.assertTrue(owner_response.data["can_manage_members"])
        self.assertEqual(owner_response.data["pending_request_count"], 0)

    def test_open_join_approves_member_immediately(self):
        self.hub.membership_policy = Hub.MembershipPolicy.OPEN
        self.hub.save(update_fields=["membership_policy"])

        response = self.client.post(
            self.membership_url(),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["membership"]["status"],
            HubMembership.Status.APPROVED,
        )
        self.assertEqual(
            response.data["membership"]["role"],
            HubMembership.Role.MEMBER,
        )
        self.assertTrue(response.data["membership"]["joined_at"])
        self.assertTrue(response.data["can_leave"])
        self.assertFalse(response.data["can_manage_members"])

    def test_approval_required_join_creates_pending_request(self):
        response = self.client.post(
            self.membership_url(),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["membership"]["status"],
            HubMembership.Status.PENDING,
        )
        self.assertEqual(
            response.data["membership"]["role"],
            HubMembership.Role.MEMBER,
        )
        self.assertIsNone(response.data["membership"]["joined_at"])
        self.assertFalse(response.data["can_leave"])

    def test_duplicate_approved_and_pending_joins_are_rejected(self):
        cases = [
            (
                Hub.MembershipPolicy.OPEN,
                HubMembership.Status.APPROVED,
                "approved hub member",
            ),
            (
                Hub.MembershipPolicy.APPROVAL_REQUIRED,
                HubMembership.Status.PENDING,
                "already pending",
            ),
        ]
        for index, (policy, expected_status, message) in enumerate(cases):
            with self.subTest(status=expected_status):
                user = self.create_user(f"duplicate_join_{index}")
                self.authenticate_as(user)
                self.hub.membership_policy = policy
                self.hub.save(update_fields=["membership_policy"])
                response = self.client.post(
                    self.membership_url(),
                    {},
                    format="json",
                )
                self.assertEqual(response.status_code, 201)
                duplicate = self.client.post(
                    self.membership_url(),
                    {},
                    format="json",
                )
                self.assertEqual(duplicate.status_code, 400)
                self.assertIn(message, str(duplicate.data).lower())

    def test_rejected_user_can_submit_a_fresh_request(self):
        rejected = self.add_membership(
            self.user,
            membership_status=HubMembership.Status.REJECTED,
        )

        response = self.client.post(
            self.membership_url(),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        rejected.refresh_from_db()
        self.assertEqual(response.data["membership"]["id"], str(rejected.id))
        self.assertEqual(rejected.status, HubMembership.Status.PENDING)
        self.assertEqual(rejected.role, HubMembership.Role.MEMBER)
        self.assertIsNone(rejected.joined_at)

    def test_inactive_hub_and_unauthenticated_join_are_rejected(self):
        inactive = Hub.objects.create(
            name="Inactive Membership Hub",
            slug="inactive-membership-hub",
            hub_type=Hub.HubType.COMMUNITY,
            created_by=self.owner,
            owner=self.owner,
            is_active=False,
        )
        inactive_response = self.client.post(
            self.membership_url(inactive),
            {},
            format="json",
        )
        self.assertEqual(inactive_response.status_code, 404)

        self.client.credentials()
        unauthenticated = self.client.post(
            self.membership_url(),
            {},
            format="json",
        )
        self.assertEqual(unauthenticated.status_code, 401)

    def test_join_rejects_protected_membership_fields(self):
        response = self.client.post(
            self.membership_url(),
            {
                "role": HubMembership.Role.ADMIN,
                "status": HubMembership.Status.APPROVED,
                "joined_at": timezone.now().isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("role", response.data)
        self.assertIn("status", response.data)
        self.assertFalse(
            HubMembership.objects.filter(hub=self.hub, user=self.user).exists()
        )

    def test_member_editor_and_admin_can_leave_but_owner_cannot(self):
        for index, role in enumerate(
            (
                HubMembership.Role.MEMBER,
                HubMembership.Role.EDITOR,
                HubMembership.Role.ADMIN,
            )
        ):
            with self.subTest(role=role):
                user = self.create_user(f"leave_user_{index}")
                membership = self.add_membership(user, role=role)
                self.authenticate_as(user)
                response = self.client.delete(self.membership_url())
                self.assertEqual(response.status_code, 204)
                self.assertFalse(
                    HubMembership.objects.filter(pk=membership.pk).exists()
                )
                self.assertTrue(Hub.objects.filter(pk=self.hub.pk).exists())

        self.authenticate_as(self.owner)
        owner_response = self.client.delete(self.membership_url())
        self.assertEqual(owner_response.status_code, 403)
        self.assertTrue(
            HubMembership.objects.filter(pk=self.owner_membership.pk).exists()
        )

    def test_pending_user_cannot_leave_without_a_cancellation_workflow(self):
        pending = self.add_membership(
            self.user,
            membership_status=HubMembership.Status.PENDING,
        )

        response = self.client.delete(self.membership_url())

        self.assertEqual(response.status_code, 400)
        self.assertTrue(HubMembership.objects.filter(pk=pending.pk).exists())

    def test_directory_lists_approved_members_only_and_hides_private_profile_data(self):
        public_user = self.create_user(
            "directory_public",
            first_name="Public",
            last_name="Member",
        )
        Profile.objects.create(
            user=public_user,
            profile_type=Profile.ProfileType.STUDENT,
            visibility=Profile.Visibility.PUBLIC,
            profile_picture="https://example.com/public.png",
        )
        private_user = self.create_user(
            "directory_private",
            first_name="Private",
            last_name="Person",
        )
        Profile.objects.create(
            user=private_user,
            profile_type=Profile.ProfileType.STUDENT,
            visibility=Profile.Visibility.PRIVATE,
            profile_picture="https://example.com/private.png",
        )
        no_profile_user = self.create_user("directory_no_profile")
        pending_user = self.create_user("directory_pending")
        rejected_user = self.create_user("directory_rejected")
        public_membership = self.add_membership(public_user)
        private_membership = self.add_membership(private_user)
        self.add_membership(no_profile_user)
        self.add_membership(
            pending_user,
            membership_status=HubMembership.Status.PENDING,
        )
        self.add_membership(
            rejected_user,
            membership_status=HubMembership.Status.REJECTED,
        )

        response = self.client.get(self.members_url())

        self.assertEqual(response.status_code, 200)
        by_id = {entry["id"]: entry for entry in response.data["results"]}
        self.assertIn(str(public_membership.id), by_id)
        self.assertIn(str(private_membership.id), by_id)
        self.assertEqual(
            by_id[str(public_membership.id)]["username"],
            "directory_public",
        )
        self.assertEqual(
            by_id[str(public_membership.id)]["profile_picture"],
            "https://example.com/public.png",
        )
        self.assertIsNone(by_id[str(private_membership.id)]["username"])
        self.assertEqual(by_id[str(private_membership.id)]["first_name"], "")
        self.assertEqual(by_id[str(private_membership.id)]["profile_picture"], "")
        self.assertTrue(
            all(
                entry["status"] == HubMembership.Status.APPROVED
                for entry in response.data["results"]
            )
        )
        self.assertNotIn("email", by_id[str(public_membership.id)])
        self.assertNotIn("user", by_id[str(public_membership.id)])
        self.assertEqual(response.data["count"], 4)

    def test_directory_is_paginated(self):
        for index in range(11):
            user = self.create_user(f"page_member_{index}")
            self.add_membership(user)

        first_page = self.client.get(self.members_url())
        second_page = self.client.get(f"{self.members_url()}?page=2")

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data["count"], 12)
        self.assertEqual(len(first_page.data["results"]), 10)
        self.assertEqual(first_page.data["next"], 2)
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(len(second_page.data["results"]), 2)
        self.assertEqual(second_page.data["previous"], 1)

    def test_only_owner_and_approved_admin_can_list_pending_requests(self):
        pending_user = self.create_user("pending_list_user")
        pending = self.add_membership(
            pending_user,
            membership_status=HubMembership.Status.PENDING,
        )

        unauthorized = self.client.get(self.requests_url())
        self.assertEqual(unauthorized.status_code, 403)

        self.authenticate_as(self.owner)
        owner_response = self.client.get(self.requests_url())
        self.assertEqual(owner_response.status_code, 200)
        self.assertEqual(owner_response.data["count"], 1)
        self.assertEqual(
            owner_response.data["results"][0]["id"],
            str(pending.id),
        )
        self.assertEqual(
            owner_response.data["results"][0]["status"],
            HubMembership.Status.PENDING,
        )

        admin = self.create_user("pending_list_admin")
        self.add_membership(admin, role=HubMembership.Role.ADMIN)
        self.authenticate_as(admin)
        admin_response = self.client.get(self.requests_url())
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(admin_response.data["count"], 1)

    def test_member_and_editor_cannot_manage_pending_requests(self):
        for role in (HubMembership.Role.MEMBER, HubMembership.Role.EDITOR):
            user = self.create_user(f"cannot_manage_{role}")
            self.add_membership(user, role=role)
            self.authenticate_as(user)
            response = self.client.get(self.requests_url())
            self.assertEqual(response.status_code, 403)

    def test_owner_and_admin_can_approve_or_reject_pending_requests(self):
        for actor_role in ("owner", "admin"):
            for decision in ("approve", "reject"):
                with self.subTest(actor=actor_role, decision=decision):
                    applicant = self.create_user(
                        f"review_{actor_role}_{decision}"
                    )
                    pending = self.add_membership(
                        applicant,
                        membership_status=HubMembership.Status.PENDING,
                    )
                    actor = self.owner
                    if actor_role == "admin":
                        actor = self.create_user(f"review_manager_{decision}")
                        self.add_membership(actor, role=HubMembership.Role.ADMIN)
                    self.authenticate_as(actor)

                    response = self.client.post(
                        self.review_url(pending, decision),
                        {},
                        format="json",
                    )

                    expected_status = (
                        HubMembership.Status.APPROVED
                        if decision == "approve"
                        else HubMembership.Status.REJECTED
                    )
                    self.assertEqual(response.status_code, 200)
                    pending.refresh_from_db()
                    self.assertEqual(pending.status, expected_status)
                    self.assertEqual(response.data["status"], expected_status)
                    self.assertEqual(pending.role, HubMembership.Role.MEMBER)
                    self.assertEqual(
                        bool(pending.joined_at),
                        decision == "approve",
                    )

    def test_only_pending_requests_can_be_processed_and_own_request_is_forbidden(self):
        approved_user = self.create_user("already_approved")
        approved = self.add_membership(approved_user)
        self.authenticate_as(self.owner)

        repeated = self.client.post(
            self.review_url(approved, "approve"),
            {},
            format="json",
        )
        self.assertEqual(repeated.status_code, 400)

        self.owner_membership.status = HubMembership.Status.PENDING
        self.owner_membership.joined_at = None
        self.owner_membership.save(update_fields=["status", "joined_at"])
        self_review = self.client.post(
            self.review_url(self.owner_membership, "approve"),
            {},
            format="json",
        )
        self.assertEqual(self_review.status_code, 403)

    def test_cross_hub_request_review_is_not_found(self):
        another_hub = Hub.objects.create(
            name="Another Membership Hub",
            slug="another-membership-hub",
            hub_type=Hub.HubType.COMMUNITY,
            created_by=self.owner,
            owner=self.owner,
        )
        applicant = self.create_user("cross_hub_applicant")
        request = self.add_membership(
            applicant,
            hub=another_hub,
            membership_status=HubMembership.Status.PENDING,
        )
        self.authenticate_as(self.owner)

        response = self.client.post(
            self.review_url(request, "approve"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        request.refresh_from_db()
        self.assertEqual(request.status, HubMembership.Status.PENDING)

    def test_owner_and_admin_can_invite_existing_users(self):
        for actor_role in ("owner", "admin"):
            invitee = self.create_user(f"invited_{actor_role}")
            actor = self.owner
            if actor_role == "admin":
                actor = self.create_user("invite_admin")
                self.add_membership(actor, role=HubMembership.Role.ADMIN)
            self.authenticate_as(actor)

            response = self.client.post(
                f"/api/hubs/{self.hub.id}/members/invitations/",
                {"username": invitee.username},
                format="json",
            )

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data["role"], HubMembership.Role.MEMBER)
            self.assertEqual(
                response.data["status"],
                HubMembership.Status.APPROVED,
            )
            self.assertNotIn("email", response.data)
            self.assertTrue(
                HubMembership.objects.filter(
                    hub=self.hub,
                    user=invitee,
                    status=HubMembership.Status.APPROVED,
                ).exists()
            )

    def test_invite_rejects_owner_duplicate_pending_and_ineligible_users(self):
        approved = self.create_user("invite_approved")
        pending = self.create_user("invite_pending")
        unverified = User.objects.create_user(
            username="invite_unverified",
            email="invite_unverified@example.com",
            password="TestPassword123!",
            email_verified=False,
        )
        self.add_membership(approved)
        self.add_membership(
            pending,
            membership_status=HubMembership.Status.PENDING,
        )

        base_url = f"/api/hubs/{self.hub.id}/members/invitations/"
        cases = (
            (self.owner.username, "owner"),
            (approved.username, "approved"),
            (pending.username, "pending"),
            (unverified.username, "unverified"),
            ("missing_user", "missing"),
        )
        self.authenticate_as(self.owner)
        for username, label in cases:
            with self.subTest(username=label):
                response = self.client.post(
                    base_url,
                    {"username": username},
                    format="json",
                )
                self.assertEqual(response.status_code, 400)

    def test_rejected_membership_can_be_reactivated_by_invitation(self):
        invitee = self.create_user("reinvited_user")
        rejected = self.add_membership(
            invitee,
            membership_status=HubMembership.Status.REJECTED,
        )
        self.authenticate_as(self.owner)

        response = self.client.post(
            f"/api/hubs/{self.hub.id}/members/invitations/",
            {"username": invitee.username},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        rejected.refresh_from_db()
        self.assertEqual(response.data["id"], str(rejected.id))
        self.assertEqual(rejected.status, HubMembership.Status.APPROVED)
        self.assertEqual(rejected.role, HubMembership.Role.MEMBER)
        self.assertTrue(rejected.joined_at)

    def test_member_and_editor_cannot_invite(self):
        target = self.create_user("invite_denied_target")
        for role in (HubMembership.Role.MEMBER, HubMembership.Role.EDITOR):
            actor = self.create_user(f"invite_denied_{role}")
            self.add_membership(actor, role=role)
            self.authenticate_as(actor)
            response = self.client.post(
                f"/api/hubs/{self.hub.id}/members/invitations/",
                {"username": target.username},
                format="json",
            )
            self.assertEqual(response.status_code, 403)
        self.assertFalse(
            HubMembership.objects.filter(hub=self.hub, user=target).exists()
        )

    def test_owner_assigns_roles_and_admin_can_only_manage_members_and_editors(self):
        target = self.create_user("role_target")
        membership = self.add_membership(target)
        role_url = (
            f"/api/hubs/{self.hub.id}/members/{membership.id}/role/"
        )
        self.authenticate_as(self.owner)

        for role in (
            HubMembership.Role.ADMIN,
            HubMembership.Role.EDITOR,
            HubMembership.Role.MEMBER,
        ):
            response = self.client.patch(
                role_url,
                {"role": role},
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            membership.refresh_from_db()
            self.assertEqual(membership.role, role)

        admin = self.create_user("role_manager_admin")
        self.add_membership(admin, role=HubMembership.Role.ADMIN)
        self.authenticate_as(admin)
        editor_response = self.client.patch(
            role_url,
            {"role": HubMembership.Role.EDITOR},
            format="json",
        )
        self.assertEqual(editor_response.status_code, 200)
        member_response = self.client.patch(
            role_url,
            {"role": HubMembership.Role.MEMBER},
            format="json",
        )
        self.assertEqual(member_response.status_code, 200)

        promote_admin = self.client.patch(
            role_url,
            {"role": HubMembership.Role.ADMIN},
            format="json",
        )
        self.assertEqual(promote_admin.status_code, 403)

        another_admin = self.create_user("protected_admin_target")
        another_admin_membership = self.add_membership(
            another_admin,
            role=HubMembership.Role.ADMIN,
        )
        admin_target_url = (
            f"/api/hubs/{self.hub.id}/members/"
            f"{another_admin_membership.id}/role/"
        )
        demote_admin = self.client.patch(
            admin_target_url,
            {"role": HubMembership.Role.MEMBER},
            format="json",
        )
        remove_admin = self.client.delete(
            f"/api/hubs/{self.hub.id}/members/"
            f"{another_admin_membership.id}/"
        )
        self.assertEqual(demote_admin.status_code, 403)
        self.assertEqual(remove_admin.status_code, 403)

    def test_owner_membership_cannot_be_removed_or_demoted(self):
        self.authenticate_as(self.owner)
        role_response = self.client.patch(
            f"/api/hubs/{self.hub.id}/members/"
            f"{self.owner_membership.id}/role/",
            {"role": HubMembership.Role.MEMBER},
            format="json",
        )
        remove_response = self.client.delete(
            f"/api/hubs/{self.hub.id}/members/"
            f"{self.owner_membership.id}/"
        )

        self.assertEqual(role_response.status_code, 403)
        self.assertEqual(remove_response.status_code, 400)
        self.owner_membership.refresh_from_db()
        self.assertEqual(
            self.owner_membership.role,
            HubMembership.Role.OWNER,
        )
        self.assertEqual(
            self.owner_membership.status,
            HubMembership.Status.APPROVED,
        )

    def test_owner_can_remove_members_and_admin_cannot_remove_admins(self):
        member = self.create_user("removable_member")
        membership = self.add_membership(member)
        self.authenticate_as(self.owner)
        removed = self.client.delete(
            f"/api/hubs/{self.hub.id}/members/{membership.id}/"
        )
        self.assertEqual(removed.status_code, 204)
        self.assertFalse(HubMembership.objects.filter(pk=membership.pk).exists())

        admin = self.create_user("remove_admin")
        self.add_membership(admin, role=HubMembership.Role.ADMIN)
        editor = self.create_user("admin_removable_editor")
        editor_membership = self.add_membership(editor, role=HubMembership.Role.EDITOR)
        self.authenticate_as(admin)
        editor_removed = self.client.delete(
            f"/api/hubs/{self.hub.id}/members/{editor_membership.id}/"
        )
        self.assertEqual(editor_removed.status_code, 204)

    def test_members_cannot_submit_protected_role_or_status_fields(self):
        target = self.create_user("protected_role_target")
        membership = self.add_membership(target)
        role_url = (
            f"/api/hubs/{self.hub.id}/members/{membership.id}/role/"
        )
        self.authenticate_as(self.owner)

        role_response = self.client.patch(
            role_url,
            {
                "role": HubMembership.Role.ADMIN,
                "status": HubMembership.Status.APPROVED,
                "user": str(self.owner.id),
            },
            format="json",
        )
        invite_response = self.client.post(
            f"/api/hubs/{self.hub.id}/members/invitations/",
            {
                "username": target.username,
                "role": HubMembership.Role.ADMIN,
                "status": HubMembership.Status.APPROVED,
            },
            format="json",
        )
        invalid_role = self.client.patch(
            role_url,
            {"role": HubMembership.Role.OWNER},
            format="json",
        )

        self.assertEqual(role_response.status_code, 400)
        self.assertIn("status", role_response.data)
        self.assertIn("user", role_response.data)
        self.assertEqual(invite_response.status_code, 400)
        self.assertIn("role", invite_response.data)
        self.assertEqual(invalid_role.status_code, 400)

        membership.refresh_from_db()
        self.assertEqual(membership.role, HubMembership.Role.MEMBER)

    def test_admin_member_and_editor_cannot_change_roles(self):
        target = self.create_user("role_permission_target")
        membership = self.add_membership(target)
        for role in (
            HubMembership.Role.MEMBER,
            HubMembership.Role.EDITOR,
        ):
            actor = self.create_user(f"role_permission_{role}")
            self.add_membership(actor, role=role)
            self.authenticate_as(actor)
            response = self.client.patch(
                f"/api/hubs/{self.hub.id}/members/{membership.id}/role/",
                {"role": HubMembership.Role.EDITOR},
                format="json",
            )
            self.assertEqual(response.status_code, 403)

    def test_unauthenticated_membership_operations_are_rejected(self):
        self.client.credentials()
        responses = [
            self.client.get(self.membership_url()),
            self.client.get(self.members_url()),
            self.client.post(self.membership_url(), {}, format="json"),
        ]
        self.assertEqual([response.status_code for response in responses], [401] * 3)
