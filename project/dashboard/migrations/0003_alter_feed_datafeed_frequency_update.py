# Generated by Django 4.2.14 on 2024-07-26 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0002_alter_feed_socratadatasetid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="feed",
            name="datafeed_frequency_update",
            field=models.DurationField(
                null=True, verbose_name="Datafeed Update Frequency"
            ),
        ),
    ]
