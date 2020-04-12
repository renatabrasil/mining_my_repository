# Generated by Django 3.0 on 2020-04-12 01:06

from django.db import migrations


class Migration(migrations.Migration):

    def update_delta_and_normalized_delta(apps, schema_editor):
        # We can't import the Person model directly as it may be a newer
        # version than this migration expects. We use the historical version.
        Commit = apps.get_model('contributions', 'Commit')
        Modification = apps.get_model('contributions', 'Modification')
        for commit in Commit.objects.filter(tag_id__gt=3):
            u_cloc = 0
            for mod in commit.modifications.all():
                u_cloc += mod.u_cloc
            commit.normalized_delta = commit.delta_rmd_components
            commit.delta_rmd_components = commit.delta_rmd_components * u_cloc
            commit.save()

    dependencies = [
        ('contributions', '0060_commit_normalized_delta'),
    ]

    operations = [
        migrations.RunPython(update_delta_and_normalized_delta),
    ]