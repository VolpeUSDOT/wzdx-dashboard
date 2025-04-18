# Generated by Django 4.2.14 on 2024-08-01 21:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0015_rename_feedstatus_status_alter_status_options"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Status",
            new_name="DataStatus",
        ),
        migrations.AlterModelOptions(
            name="datastatus",
            options={
                "ordering": ["-datetime_checked"],
                "verbose_name_plural": "data statuses",
            },
        ),
    ]
