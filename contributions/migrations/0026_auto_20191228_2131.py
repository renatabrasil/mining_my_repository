# Generated by Django 3.0 on 2019-12-29 00:31

import datetime

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0025_auto_20191228_1900'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commit',
            name='children_commit',
        ),
        migrations.AlterField(
            model_name='commit',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='author',
                                    to='contributions.Developer'),
        ),
        migrations.AlterField(
            model_name='commit',
            name='author_date',
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name='commit',
            name='committer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='committer',
                                    to='contributions.Developer'),
        ),
        migrations.AlterField(
            model_name='commit',
            name='committer_date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
