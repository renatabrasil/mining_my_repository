# Generated by Django 3.0 on 2020-02-04 17:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0043_directory_initial_commit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='directory',
            name='initial_commit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='starter_directories', to='contributions.Commit'),
        ),
    ]
