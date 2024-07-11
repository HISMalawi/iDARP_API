# Generated by Django 4.2.7 on 2024-07-02 14:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_dictionary', '0011_version'),
    ]

    operations = [
        migrations.CreateModel(
            name='VersionVariable',
            fields=[
                ('version_variable_id', models.AutoField(primary_key=True, serialize=False)),
                ('variable', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='variables', to='data_dictionary.variable')),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='versions', to='data_dictionary.version')),
            ],
            options={
                'db_table': 'version_variables',
                'managed': True,
            },
        ),
    ]
