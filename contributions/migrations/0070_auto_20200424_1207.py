# Generated by Django 3.0 on 2020-04-24 15:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0069_auto_20200417_1315'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComponentCommit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_experience', models.FloatField(default=0.0, null=True)),
                ('commit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='component_commits', to='contributions.Commit')),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='component_commits', to='contributions.Directory')),
            ],
        ),
        migrations.AddField(
            model_name='modification',
            name='component_commit',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='modifications', to='contributions.ComponentCommit'),
            preserve_default=False,
        ),
    ]
