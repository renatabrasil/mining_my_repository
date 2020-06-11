# Generated by Django 3.0 on 2020-04-15 19:07

from django.db import migrations

from architecture.views import SCALE


class Migration(migrations.Migration):

    def update_delta_and_normalized_delta_with_rounding(apps, schema_editor):
        # We can't import the Person model directly as it may be a newer
        # version than this migration expects. We use the historical version.
        Commit = apps.get_model('contributions', 'Commit')
        ArchitecturalMetricsByCommit = apps.get_model('architecture', 'ArchitecturalMetricsByCommit')

        for commit in Commit.objects.all():
            commit.normalized_delta = 0.0 if round(commit.normalized_delta, SCALE) == 0.0 else commit.normalized_delta
            commit.delta_rmd_components = 0.0 if round(commit.delta_rmd_components, SCALE) == 0.0 else commit.delta_rmd_components
            commit.save()

        for metric in ArchitecturalMetricsByCommit.objects.all():
            metric.delta_rmd = 0.0 if round(metric.delta_rmd, SCALE) == 0.0 else metric.delta_rmd
            metric.save()

    dependencies = [
        ('contributions', '0061_auto_20200411_2206'),
    ]

    operations = [
        migrations.RunPython(update_delta_and_normalized_delta_with_rounding),
    ]