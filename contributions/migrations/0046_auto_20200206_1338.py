# Generated by Django 3.0 on 2020-02-06 16:38

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0045_auto_20200206_1337'),
    ]

    operations = [
        migrations.RenameField(
            model_name='commit',
            old_name='delta_total_rmd',
            new_name='delta_rmd_components',
        ),
        migrations.RenameField(
            model_name='commit',
            old_name='mean_rmd',
            new_name='mean_rmd_components',
        ),
        migrations.RenameField(
            model_name='commit',
            old_name='std_rmd',
            new_name='std_rmd_components',
        ),
    ]
