# Generated by Django 3.0 on 2020-05-18 02:44

from django.db import migrations, models


class Migration(migrations.Migration):
    def update_compilable_cassandra(apps, schema_editor):
        # We can't import the Person model directly as it may be a newer
        # version than this migration expects. We use the historical version.
        tag = apps.get_model('contributions', 'Tag')
        project = apps.get_model('contributions', 'Project')
        commit = apps.get_model('contributions', 'Commit')

    dependencies = [
        ('contributions', '0083_auto_20200517_1149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commit',
            name='compilable',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(update_compilable_cassandra),
    ]
