# Generated by Django 4.2.7 on 2023-11-30 13:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_requests', '0008_reply'),
    ]

    operations = [
        migrations.AddField(
            model_name='statecomment',
            name='data_request',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='data_requests.datarequest'),
        ),
    ]
