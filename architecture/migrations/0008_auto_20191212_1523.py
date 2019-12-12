# Generated by Django 3.0 on 2019-12-12 18:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0018_auto_20191202_1142'),
        ('architecture', '0007_delete_compiled'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='filecommits',
            name='project',
        ),
        migrations.AddField(
            model_name='filecommits',
            name='tag',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='contributions.Tag'),
            preserve_default=False,
        ),
    ]