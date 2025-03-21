# Generated by Django 4.2.14 on 2024-08-07 19:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0027_remove_feed_is_online_feed_response_code"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeedData",
            fields=[
                (
                    "feed",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="dashboard.feed",
                    ),
                ),
                (
                    "response_code",
                    models.IntegerField(default=0, verbose_name="HTML Response Code"),
                ),
                (
                    "last_checked",
                    models.DateTimeField(auto_now=True, verbose_name="Last Updated"),
                ),
                ("feed_data", models.JSONField(default=dict, verbose_name="Feed Data")),
            ],
        ),
        migrations.RemoveField(
            model_name="feed",
            name="feed_data",
        ),
        migrations.RemoveField(
            model_name="feed",
            name="last_checked",
        ),
        migrations.RemoveField(
            model_name="feed",
            name="response_code",
        ),
    ]
