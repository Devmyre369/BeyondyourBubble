from django.contrib import admin

# Register your models here.

from django.contrib import admin

from .models import Moment, Vibe


@admin.register(Vibe)
class VibeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "event",
        "created_at",
    )

    list_filter = ("created_at",)

    search_fields = (
        "text",
        "author__username",
        "author__email",
        "event__title",
    )

    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Moment)
class MomentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "event",
        "caption",
        "created_at",
    )

    list_filter = ("created_at",)

    search_fields = (
        "caption",
        "author__username",
        "author__email",
        "event__title",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
