# Generated by Django 2.2.5 on 2019-10-13 18:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0003_directoryreport_experience_threshold'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='directoryreport',
            name='tag',
        ),
        migrations.AddField(
            model_name='individualcontribution',
            name='tag',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING,
                                    related_name='directory_reports', to='contributions.Tag'),
            preserve_default=False,
        ),
    ]
