
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Profile, PendingSignup, EmailOTP


# ==================================================
# USER ADMIN
# ==================================================

@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "username",
        "email",
        "email_verified",
        "onboarding_completed",
        "is_staff",
        "is_active",
    )

    search_fields = ("username", "email")

    list_filter = (
        "email_verified",
        "onboarding_completed",
        "is_staff",
        "is_active",
    )

    fieldsets = UserAdmin.fieldsets + (
        ("BYB Account Information", {
            "fields": (
                "email_verified",
                "onboarding_completed",
            ),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("BYB Account Information", {
            "fields": (
                "email",
                "email_verified",
                "onboarding_completed",
            ),
        }),
    )


# ==================================================
# PROFILE ADMIN
# ==================================================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "profile_type",
        "city",
        "visibility",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "byb_signature",
        "city",
        "institution",
        "current_organization",
    )

    list_filter = (
        "profile_type",
        "visibility",
        "created_at",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Account", {
            "fields": ("id", "user", "profile_type"),
        }),
        ("Personal Identity", {
            "fields": (
                "byb_signature",
                "bio",
                "city",
                "profile_picture",
                "cover_image",
            ),
        }),
        ("Student Information", {
            "fields": (
                "institution",
                "course",
                "field_of_study",
                "academic_year",
                "graduation_year",
            ),
        }),
        ("Professional Information", {
            "fields": (
                "current_organization",
                "job_title",
                "industry",
                "experience_years",
            ),
        }),
        ("Interests and Skills", {
            "fields": ("interests", "skills"),
        }),
        ("Social Links", {
            "fields": (
                "linkedin_url",
                "github_url",
                "website_url",
            ),
        }),
        ("Privacy and Timestamps", {
            "fields": (
                "visibility",
                "created_at",
                "updated_at",
            ),
        }),
    )


# ==================================================
# PENDING SIGNUP ADMIN
# ==================================================

@admin.register(PendingSignup)
class PendingSignupAdmin(admin.ModelAdmin):

    list_display = (
        "username",
        "email",
        "created_at",
        "expires_at",
    )

    search_fields = ("username", "email")


# ==================================================
# EMAIL OTP ADMIN
# ==================================================

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):

    list_display = (
        "email",
        "purpose",
        "attempts",
        "expires_at",
        "is_used",
    )

    search_fields = ("email",)

    list_filter = (
        "purpose",
        "is_used",
    )
