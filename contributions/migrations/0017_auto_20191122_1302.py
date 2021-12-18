# Generated by Django 2.2.5 on 2019-11-22 16:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0016_commit_children_commit'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectIndividualContribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cloc', models.IntegerField(default=0, null=True)),
                ('files', models.IntegerField(default=0, null=True)),
                ('commits', models.IntegerField(default=0, null=True)),
                ('ownership_cloc', models.FloatField(default=0.0, null=True)),
                ('ownership_cloc_in_this_tag', models.FloatField(default=0.0, null=True)),
                ('cloc_exp', models.FloatField(default=0.0, null=True)),
                ('ownership_files', models.FloatField(default=0.0, null=True)),
                ('ownership_files_in_this_tag', models.FloatField(default=0.0, null=True)),
                ('file_exp', models.FloatField(default=0.0, null=True)),
                ('ownership_commits', models.FloatField(default=0.0, null=True)),
                ('ownership_commits_in_this_tag', models.FloatField(default=0.0, null=True)),
                ('commit_exp', models.FloatField(default=0.0, null=True)),
                ('experience', models.FloatField(default=0.0, null=True)),
                ('experience_bf', models.FloatField(default=0.0, null=True)),
                ('abs_experience', models.FloatField(default=0.0, null=True)),
                ('bf_commit', models.FloatField(default=0.0, null=True)),
                ('bf_file', models.FloatField(default=0.0, null=True)),
                ('bf_cloc', models.FloatField(default=0.0, null=True)),
                ('author',
                 models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='contributions.Developer')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_cloc', models.IntegerField(default=0, null=True)),
                ('total_files', models.IntegerField(default=0, null=True)),
                ('total_commits', models.IntegerField(default=0, null=True)),
                ('cloc_threshold', models.FloatField(default=0.0, null=True)),
                ('file_threshold', models.FloatField(default=0.0, null=True)),
                ('commit_threshold', models.FloatField(default=0.0, null=True)),
                ('experience_threshold', models.FloatField(default=0.0, null=True)),
                ('standard_deviation', models.FloatField(default=0, null=True)),
                ('mean', models.FloatField(default=0, null=True)),
                ('median', models.FloatField(default=0, null=True)),
                ('authors', models.ManyToManyField(through='contributions.ProjectIndividualContribution',
                                                   to='contributions.Developer')),
                ('tag',
                 models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='project_reports',
                                   to='contributions.Tag')),
            ],
        ),
        migrations.AddField(
            model_name='projectindividualcontribution',
            name='project_report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='contributions.ProjectReport'),
        ),
    ]
