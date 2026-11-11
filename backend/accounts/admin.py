from django.contrib import admin

# Register your models here.


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, EmailOTP


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "email_verified",
        "is_staff",
        "is_active",
    )

    search_fields = ("username", "email")

    fieldsets = UserAdmin.fieldsets + (
        ("BYB Account Information", {
            "fields": ("email_verified",),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("BYB Account Information", {
            "fields": ("email", "email_verified"),
        }),
    )


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
    list_filter = ("purpose", "is_used")
