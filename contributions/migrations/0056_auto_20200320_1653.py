# Generated by Django 3.0 on 2020-03-20 19:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0053_auto_20200213_1119'),
    ]

    operations = [
        migrations.AddField(
            model_name='commit',
            name='author_seniority',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='commit',
            name='total_commits',
            field=models.IntegerField(default=0),
        ),
    ]
