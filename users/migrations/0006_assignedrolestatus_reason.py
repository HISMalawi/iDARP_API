# Generated by Django 4.2.7 on 2024-07-03 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_orgrolestatus_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignedrolestatus',
            name='Reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
