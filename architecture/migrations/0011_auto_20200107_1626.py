# Generated by Django 3.0 on 2020-01-07 19:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0038_commit_cloc_activity_str'),
        ('architecture', '0010_auto_20200107_1624'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='architecturequalitymetrics',
            name='id',
        ),
        migrations.AlterField(
            model_name='architecturequalitymetrics',
            name='commit',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='architectural_metric', serialize=False, to='contributions.Commit'),
        ),
    ]
