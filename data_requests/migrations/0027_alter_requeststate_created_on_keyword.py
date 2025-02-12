# Generated by Django 4.2.7 on 2024-02-26 12:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
        ('data_requests', '0026_rename_notifications_count_requeststate_reminders_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requeststate',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('keyword_id', models.AutoField(primary_key=True, serialize=False)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_requests.datarequest')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analytics.tag')),
            ],
            options={
                'db_table': 'keywords',
                'managed': True,
            },
        ),
    ]
