from django.contrib import admin
from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Hub, HubMembership, HubApplication, HubVerificationRequest
from .services.application_service import (
    approve_application,
    reject_application,
)


@admin.register(Hub)
class HubAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "hub_type",
        "owner",
        "created_by",
        "is_verified",
        "is_active",
        "created_at",
    )
    list_filter = (
        "hub_type",
        "is_verified",
        "is_active",
        "created_at",
    )
    search_fields = (
        "name",
        "slug",
        "city",
        "college_or_parent_organisation",
    )
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("created_by", "owner")
    date_hierarchy = "created_at"
    readonly_fields = ("is_verified",)


@admin.register(HubMembership)
class HubMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "hub",
        "role",
        "status",
        "joined_at",
        "created_at",
    )
    list_filter = (
        "role",
        "status",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "hub__name",
        "hub__slug",
    )
    raw_id_fields = ("hub", "user")
    date_hierarchy = "created_at"


@admin.register(HubApplication)
class HubApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "requested_name",
        "requested_slug",
        "applicant",
        "hub_type",
        "status",
        "reviewer",
        "reviewed_at",
        "created_at",
    )
    list_filter = (
        "status",
        "hub_type",
        "created_at",
    )
    search_fields = (
        "applicant__username",
        "applicant__email",
        "requested_name",
        "requested_slug",
    )
    raw_id_fields = ("applicant", "reviewer")
    readonly_fields = (
        "applicant",
        "requested_name",
        "requested_slug",
        "hub_type",
        "organisation_description",
        "college_or_parent_organisation",
        "city",
        "website",
        "contact_email",
        "status",
        "reviewer",
        "review_notes",
        "reviewed_at",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"
    actions = ["approve_selected", "reject_selected"]

    def has_add_permission(self, request):
        # Applications are created through the application workflow, not
        # directly in the admin.
        return False

    @admin.action(description=_("Approve selected applications"))
    def approve_selected(self, request, queryset):
        if not request.user.is_staff:
            self.message_user(
                request,
                "Only authorised BYB staff can approve applications.",
                level=messages.ERROR,
            )
            return

        approved = 0
        skipped = 0

        for application in queryset:
            if application.status != HubApplication.Status.PENDING:
                skipped += 1
                continue

            try:
                approve_application(application, request.user)
                approved += 1
            except (PermissionDenied, ValidationError):
                skipped += 1

        self.message_user(
            request,
            f"Approved {approved} application(s). "
            f"{skipped} application(s) were skipped "
            "(not pending or already reviewed).",
            level=messages.SUCCESS,
        )

    @admin.action(description=_("Reject selected applications"))
    def reject_selected(self, request, queryset):
        if not request.user.is_staff:
            self.message_user(
                request,
                "Only authorised BYB staff can reject applications.",
                level=messages.ERROR,
            )
            return

        if request.POST.get("confirm_reject") != "yes":
            return TemplateResponse(
                request,
                "admin/hubs/hubapplication/reject_selected_confirmation.html",
                {"applications": queryset, "opts": self.model._meta},
            )

        review_notes = request.POST.get("review_notes", "").strip()
        if not review_notes:
            self.message_user(
                request,
                "A rejection reason is required.",
                level=messages.ERROR,
            )
            return TemplateResponse(
                request,
                "admin/hubs/hubapplication/reject_selected_confirmation.html",
                {
                    "applications": queryset,
                    "opts": self.model._meta,
                    "error": "Enter a rejection reason.",
                },
            )

        rejected = 0
        skipped = 0

        for application in queryset:
            if application.status != HubApplication.Status.PENDING:
                skipped += 1
                continue

            try:
                reject_application(
                    application,
                    request.user,
                    review_notes=review_notes,
                )
                rejected += 1
            except (PermissionDenied, ValidationError):
                skipped += 1

        self.message_user(
            request,
            f"Rejected {rejected} application(s). "
            f"{skipped} application(s) were skipped "
            "(not pending or already reviewed).",
            level=messages.SUCCESS,
        )


@admin.register(HubVerificationRequest)
class HubVerificationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "hub", "requested_by", "status", "reviewer", "requested_at", "reviewed_at",
    )
    list_filter = ("status", "requested_at", "reviewed_at")
    search_fields = ("hub__name", "hub__slug", "requested_by__username")
    raw_id_fields = ("hub", "requested_by", "reviewer")
    readonly_fields = (
        "hub", "requested_by", "request_notes", "status", "reviewer",
        "review_notes", "requested_at", "reviewed_at",
    )
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_staff)

    def has_delete_permission(self, request, obj=None):
        return False
