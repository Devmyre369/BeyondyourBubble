from django.urls import path

from .views import (
    HubDetailView,
    HubDiscoveryView,
    HubMemberInviteView,
    HubMemberRemoveView,
    HubMemberRoleView,
    HubMembersView,
    HubMembershipRequestReviewView,
    HubMembershipView,
    HubPendingRequestsView,
)


urlpatterns = [
    path("", HubDiscoveryView.as_view(), name="hub-list"),
    path(
        "<uuid:hub_id>/membership/",
        HubMembershipView.as_view(),
        name="hub-membership",
    ),
    path(
        "<uuid:hub_id>/members/",
        HubMembersView.as_view(),
        name="hub-members",
    ),
    path(
        "<uuid:hub_id>/members/requests/",
        HubPendingRequestsView.as_view(),
        name="hub-pending-requests",
    ),
    path(
        "<uuid:hub_id>/members/requests/<uuid:membership_id>/approve/",
        HubMembershipRequestReviewView.as_view(),
        {"decision": "approve"},
        name="hub-membership-approve",
    ),
    path(
        "<uuid:hub_id>/members/requests/<uuid:membership_id>/reject/",
        HubMembershipRequestReviewView.as_view(),
        {"decision": "reject"},
        name="hub-membership-reject",
    ),
    path(
        "<uuid:hub_id>/members/invitations/",
        HubMemberInviteView.as_view(),
        name="hub-member-invite",
    ),
    path(
        "<uuid:hub_id>/members/<uuid:membership_id>/role/",
        HubMemberRoleView.as_view(),
        name="hub-member-role",
    ),
    path(
        "<uuid:hub_id>/members/<uuid:membership_id>/",
        HubMemberRemoveView.as_view(),
        name="hub-member-remove",
    ),
    path("<uuid:hub_id>/", HubDetailView.as_view(), name="hub-detail"),
]
