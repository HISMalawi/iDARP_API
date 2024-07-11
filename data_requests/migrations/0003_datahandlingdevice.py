# Generated by Django 4.1 on 2023-10-19 13:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_requests', '0002_datarequest_ethics_committee_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataHandlingDevice',
            fields=[
                ('device_id', models.AutoField(primary_key=True, serialize=False)),
                ('equipment_type', models.CharField(max_length=255)),
                ('serial_number', models.CharField(max_length=100)),
                ('used_by', models.CharField(max_length=200)),
                ('organisation', models.CharField(max_length=255)),
                ('usage_from', models.DateField()),
                ('usage_to', models.DateField()),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_requests.datarequest')),
            ],
            options={
                'db_table': 'data_handling_devices',
                'managed': True,
            },
        ),
    ]
