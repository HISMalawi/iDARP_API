# Generated by Django 4.2.7 on 2024-02-28 13:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_dictionary', '0006_rename_type_tablemetadata_val_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='VariableMetadata',
            fields=[
                ('metadata_id', models.AutoField(primary_key=True, serialize=False)),
                ('key', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
                ('val_type', models.CharField(max_length=255)),
                ('variable', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='variable', to='data_dictionary.variable')),
            ],
            options={
                'db_table': 'variable_metadata',
                'managed': True,
            },
        ),
    ]
