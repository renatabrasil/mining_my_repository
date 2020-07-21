# Generated by Django 3.0 on 2020-02-17 19:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0055_commit_analysis_period'),
        ('dataanalysis', '0003_auto_20200217_1615'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisperiod',
            name='end_commit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='analysis_period_ending', to='contributions.Commit'),
        ),
        migrations.AlterField(
            model_name='analysisperiod',
            name='start_commit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='analysis_period_beginning', to='contributions.Commit'),
        ),
    ]
