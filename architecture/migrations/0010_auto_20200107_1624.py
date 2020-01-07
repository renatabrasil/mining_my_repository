# Generated by Django 3.0 on 2020-01-07 19:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0038_commit_cloc_activity_str'),
        ('architecture', '0009_auto_20191220_1412'),
    ]

    operations = [
        migrations.AlterField(
            model_name='architecturequalitymetrics',
            name='commit',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='architectural_metric', to='contributions.Commit'),
        ),
    ]
