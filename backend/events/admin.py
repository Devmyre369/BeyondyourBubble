from django.contrib import admin

# Register your models here.

from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "organiser",
        "status",
        "city",
        "starts_at",
        "created_at",
    )

    list_filter = ("status", "city", "created_at")

    search_fields = (
        "title",
        "description",
        "city",
        "organiser__username",
    )

    readonly_fields = ("id", "created_at", "updated_at")
