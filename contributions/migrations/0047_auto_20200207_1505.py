# Generated by Django 3.0 on 2020-02-07 18:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0046_auto_20200206_1338'),
    ]

    operations = [
        migrations.RenameField(
            model_name='commit',
            old_name='delta_rmd_components',
            new_name='delta_rmd',
        ),
    ]