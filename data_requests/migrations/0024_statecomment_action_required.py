# Generated by Django 4.2.7 on 2024-01-31 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_requests', '0023_datahandlingdevice_equipment_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='statecomment',
            name='action_required',
            field=models.BooleanField(default=False),
        ),
    ]
