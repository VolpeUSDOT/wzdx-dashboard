# Generated by Django 4.2.14 on 2024-08-01 23:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "dashboard",
            "0018_alter_outdatederror_options_alter_staleerror_options_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="outdatederror",
            name="update_date",
            field=models.DateTimeField(verbose_name="Outdated Update Date"),
        ),
    ]
