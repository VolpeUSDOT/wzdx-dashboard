# Generated by Django 4.2.14 on 2024-07-26 03:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="feed",
            name="socratadatasetid",
            field=models.TextField(
                blank=True, default="", verbose_name="Socrata Dataset ID"
            ),
            preserve_default=False,
        ),
    ]
