# Generated by Django 4.2.7 on 2024-01-22 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_requests', '0017_rename_irb_id_datarequest_irb'),
    ]

    operations = [
        migrations.AddField(
            model_name='requesteddataset',
            name='filters',
            field=models.TextField(blank=True, null=True),
        ),
    ]
