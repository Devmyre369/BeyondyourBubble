from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0005_eventregistration"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="review_category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("incomplete", "Incomplete information"),
                    ("unverifiable", "Invalid or unverifiable details"),
                    ("duplicate", "Duplicate event"),
                    ("misleading", "Misleading information"),
                    ("policy_violation", "Policy violation"),
                    ("inappropriate", "Inappropriate content"),
                    ("other", "Other"),
                ],
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="eventmoderationreview",
            name="review_category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("incomplete", "Incomplete information"),
                    ("unverifiable", "Invalid or unverifiable details"),
                    ("duplicate", "Duplicate event"),
                    ("misleading", "Misleading information"),
                    ("policy_violation", "Policy violation"),
                    ("inappropriate", "Inappropriate content"),
                    ("other", "Other"),
                ],
                max_length=24,
            ),
        ),
    ]
