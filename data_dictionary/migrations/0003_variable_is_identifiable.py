# Generated by Django 4.1 on 2023-10-11 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_dictionary', '0002_variable_value_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='variable',
            name='is_identifiable',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
