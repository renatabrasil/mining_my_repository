# Generated by Django 3.0 on 2019-12-29 00:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0027_auto_20191228_2136'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commit',
            name='committer',
        ),
        migrations.RemoveField(
            model_name='commit',
            name='hash',
        ),
        migrations.RemoveField(
            model_name='commit',
            name='msg',
        ),
        migrations.RemoveField(
            model_name='commit',
            name='parents_str',
        ),
    ]
