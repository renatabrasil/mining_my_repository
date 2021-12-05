# Generated by Django 3.0 on 2020-04-27 14:27

from django.db import migrations


class Migration(migrations.Migration):

    def fix_negative_seniority(apps, schema_editor):
        # We can't import the Person model directly as it may be a newer
        # version than this migration expects. We use the historical version.
        commit = apps.get_model('contributions', 'Commit')

        for commit in commit.objects.filter(tag__project_id=2, author_seniority__lt=0):
            commit.author_seniority = abs(commit.author_seniority)
            commit.save()

    dependencies = [
        ('contributions', '0072_auto_20200424_1608'),
    ]

    operations = [
        migrations.RunPython(fix_negative_seniority),
    ]
