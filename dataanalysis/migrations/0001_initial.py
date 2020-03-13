# Generated by Django 3.0 on 2020-02-17 16:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contributions', '0054_commit_changed_architecture'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisPeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('end_commit', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analysis_period_ending', to='contributions.Commit')),
                ('start_commit', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analysis_period_beginning', to='contributions.Commit')),
            ],
        ),
    ]