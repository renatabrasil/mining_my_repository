# Generated by Django 3.0 on 2020-01-07 20:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0038_commit_cloc_activity_str'),
        ('architecture', '0011_auto_20200107_1626'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchitecturalMetricsByCommit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rmd', models.FloatField(default=0.0, null=True)),
                ('rma', models.FloatField(default=0.0, null=True)),
                ('rmi', models.FloatField(default=0.0, null=True)),
                ('ca', models.IntegerField(default=0, null=True)),
                ('ce', models.IntegerField(default=0, null=True)),
                ('commit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='architectural_metrics', to='contributions.Commit')),
                ('directory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='architectural_metrics', to='contributions.Directory')),
                ('previous_architecture_quality_metrics', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='architecture.ArchitecturalMetricsByCommit')),
            ],
        ),
        migrations.DeleteModel(
            name='ArchitectureQualityMetrics',
        ),
    ]