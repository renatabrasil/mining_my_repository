# Generated by Django 3.0 on 2020-05-25 23:42

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0086_auto_20200525_2038'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tag',
            name='metrics_calculated_at',
        ),
    ]
