# Generated by Django 4.1 on 2023-08-18 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djtrigger', '0007_auto_20201001_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trigger',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='triggerresult',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
