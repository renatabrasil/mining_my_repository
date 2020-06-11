# Generated by Django 3.0 on 2020-04-29 01:17

from django.db import migrations


class Migration(migrations.Migration):

    def fix_experience(apps, schema_editor):
        # We can't import the Person model directly as it may be a newer
        # version than this migration expects. We use the historical version.
        Commit = apps.get_model('contributions', 'Commit')
        Modification = apps.get_model('contributions', 'Modification')

        for commit in Commit.objects.filter(tag_id=23).order_by('id'):
            if len(commit.modifications.all()) == 0:
                instance = Commit.objects.get(id=commit.id)
                instance.delete()

    dependencies = [
        ('contributions', '0074_auto_20200428_1742'),
    ]

    operations = [
        migrations.RunPython(fix_experience),
    ]