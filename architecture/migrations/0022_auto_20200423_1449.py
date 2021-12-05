# Generated by Django 3.0 on 2020-04-23 17:49

from django.db import migrations


class Migration(migrations.Migration):

    def update_author_experience_in_components(apps, schema_editor):
        # We can't import the Person model directly as it may be a newer
        # version than this migration expects. We use the historical version.
        architectural_metrics_by_commit = apps.get_model('architecture', 'ArchitecturalMetricsByCommit')
        modification = apps.get_model('contributions', 'Modification')

        for component in architectural_metrics_by_commit.objects.all():
            component.commits_accumulation = 0
            component.cloc_accumulation = 0
            commits_accumulation = 0
            cloc_accumulation = 0
            previous_contribution_to_component = None

            previous_contribution_to_component = architectural_metrics_by_commit.objects.filter(
                commit__author=component.commit.author,
                directory=component.directory,
                commit__tag__lte=component.commit.tag.id,
                id__lt=component.id).last()

            cloc = 0
            for mod in component.commit.modifications.all():
                # if mod.directory == directory:
                if mod.directory.name.startswith(component.directory.name):
                    cloc += mod.u_cloc

            # because components are saved directly
            if previous_contribution_to_component is not None:
                commits_accumulation = previous_contribution_to_component.commits_accumulation
                cloc_accumulation = previous_contribution_to_component.cloc_accumulation
                component.commits_accumulation = commits_accumulation + 1
                component.cloc_accumulation = cloc_accumulation + cloc

            file_by_authors = modification.objects.none()
            if commits_accumulation > 0:
                # because Modification model imply any directory whether they are components or not
                file_by_authors = modification.objects.filter(commit__author=component.commit.author,
                                                              commit__tag_id__lte=component.commit.tag.id,
                                                              id__lt=component.id,
                                                              directory__name__startswith=component.directory.name)

            files = file_by_authors.values("path").distinct().count()

            component.author_experience = 0.2 * commits_accumulation + 0.4 * files + 0.4 * cloc_accumulation

            component.save()

    dependencies = [
        ('architecture', '0015_auto_20200423_1052'),
    ]

    operations = [
        migrations.RunPython(update_author_experience_in_components),
    ]
