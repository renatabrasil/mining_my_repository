# Generated by Django 2.2.5 on 2019-10-13 16:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0002_auto_20191013_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='directoryreport',
            name='experience_threshold',
            field=models.FloatField(default=0.0, null=True),
        ),
    ]
