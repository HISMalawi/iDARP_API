# Generated by Django 4.2.7 on 2024-02-29 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_requests', '0027_alter_requeststate_created_on_keyword'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staffshared',
            name='identification_file_path',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
