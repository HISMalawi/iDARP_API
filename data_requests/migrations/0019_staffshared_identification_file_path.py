# Generated by Django 4.2.7 on 2024-01-25 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_requests', '0018_requesteddataset_filters'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffshared',
            name='identification_file_path',
            field=models.CharField(blank=True, max_length=265, null=True),
        ),
    ]
