# Generated by Django 4.2.14 on 2024-08-02 00:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0020_alter_schemaerror_schema_error_field_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schemaerror',
            name='schema_error_field',
            field=models.TextField(blank=True, verbose_name='Schema Error Field'),
        ),
        migrations.AlterField(
            model_name='schemaerror',
            name='schema_error_type',
            field=models.TextField(blank=True, verbose_name='Schema Error Type'),
        ),
    ]
