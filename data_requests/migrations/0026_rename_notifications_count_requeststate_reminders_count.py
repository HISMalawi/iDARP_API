# Generated by Django 4.2.7 on 2024-02-13 07:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_requests', '0025_remove_statecomment_data_request'),
    ]

    operations = [
        migrations.RenameField(
            model_name='requeststate',
            old_name='notifications_count',
            new_name='reminders_count',
        ),
    ]
