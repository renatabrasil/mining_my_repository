# Generated by Django 3.0 on 2020-05-25 23:35

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0083_auto_20200517_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='metrics_calculated_at',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
    ]
