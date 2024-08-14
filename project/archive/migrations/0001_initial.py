# Generated by Django 4.2.14 on 2024-08-14 19:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("dashboard", "0028_feeddata_remove_feed_feed_data_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeedArchive",
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
                ("datetime_archived", models.DateTimeField(auto_now_add=True)),
                ("data", models.JSONField(default=dict)),
                (
                    "feed",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="dashboard.feed"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "feed archives",
                "ordering": ["-datetime_archived"],
            },
        ),
    ]
