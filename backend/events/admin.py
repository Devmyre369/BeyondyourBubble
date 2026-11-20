
from django.contrib import admin

from .models import Event, EventModerationReview


class EventModerationReviewInline(admin.TabularInline):
    model = EventModerationReview
    extra = 0
    can_delete = False
    readonly_fields = ("reviewer", "decision", "review_notes", "reviewed_at")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    inlines = (EventModerationReviewInline,)
    list_display = (
        "title",
        "organising_hub",
        "created_by",
        "category",
        "format",
        "status",
        "moderation_status",
        "city",
        "starts_at",
        "created_at",
    )

    list_filter = (
        "status",
        "moderation_status",
        "category",
        "format",
        "city",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "city",
        "organising_hub__name",
        "created_by__username",
        "created_by__email",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "organising_hub",
        "created_by",
        "reviewed_by",
    )

    ordering = ("-created_at",)
