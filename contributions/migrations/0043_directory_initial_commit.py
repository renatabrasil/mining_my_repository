# Generated by Django 3.0 on 2020-01-30 16:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0042_auto_20200123_1005'),
    ]

    operations = [
        migrations.AddField(
            model_name='directory',
            name='initial_commit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='starter_directories', to='contributions.Commit'),
        ),
    ]
