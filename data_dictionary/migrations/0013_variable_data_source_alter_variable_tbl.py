# Generated by Django 4.2.7 on 2024-07-02 14:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_dictionary', '0012_versionvariable'),
    ]

    operations = [
        migrations.AddField(
            model_name='variable',
            name='data_source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='data_dictionary.datasource'),
        ),
        migrations.AlterField(
            model_name='variable',
            name='tbl',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='var', to='data_dictionary.table'),
        ),
    ]
