import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def preserve_existing_review(apps, schema_editor):
    Event = apps.get_model("events", "Event")
    Review = apps.get_model("events", "EventModerationReview")
    database = schema_editor.connection.alias
    for event in Event.objects.using(database).exclude(reviewed_at__isnull=True).iterator():
        decision = "approved" if event.moderation_status == "approved" else "rejected"
        review = Review.objects.using(database).create(
            event_id=event.pk,
            reviewer_id=event.reviewed_by_id,
            decision=decision,
            review_notes=event.review_notes,
        )
        Review.objects.using(database).filter(pk=review.pk).update(
            reviewed_at=event.reviewed_at,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0003_alter_event_created_by_alter_event_organising_hub"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EventModerationReview",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "decision",
                    models.CharField(
                        choices=[("approved", "Approved"), ("rejected", "Rejected")],
                        max_length=10,
                    ),
                ),
                ("review_notes", models.TextField(blank=True)),
                ("reviewed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moderation_history",
                        to="events.event",
                    ),
                ),
                (
                    "reviewer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="event_moderation_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-reviewed_at"]},
        ),
        migrations.RunPython(preserve_existing_review, migrations.RunPython.noop),
    ]
