# Generated by Django 3.2.7 on 2021-12-05 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0096_auto_20200721_2134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commit',
            name='compilable',
            field=models.BooleanField(default=False),
        ),
    ]
