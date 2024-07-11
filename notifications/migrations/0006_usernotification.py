# Generated by Django 4.1 on 2023-09-26 17:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('notifications', '0005_requestnotification'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserNotification',
            fields=[
                ('user_notification_id', models.AutoField(primary_key=True, serialize=False)),
                ('assigned_role', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='users.assignedrole')),
                ('request_notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notifications.requestnotification')),
            ],
            options={
                'db_table': 'user_notifications',
                'managed': True,
            },
        ),
    ]
