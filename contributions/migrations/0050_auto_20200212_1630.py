# Generated by Django 3.0 on 2020-02-12 19:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0049_developer_login'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commit',
            name='cloc_activity_str',
        ),
        migrations.AddField(
            model_name='commit',
            name='architecture_change',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='commit',
            name='cloc_activity',
            field=models.IntegerField(default=0),
        ),
    ]
