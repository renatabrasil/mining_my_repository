# Generated by Django 3.0 on 2020-04-17 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0067_auto_20200416_1904'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='major',
            field=models.BooleanField(default=True),
        ),
    ]
