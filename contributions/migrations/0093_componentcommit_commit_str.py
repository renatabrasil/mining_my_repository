# Generated by Django 3.0.8 on 2020-07-14 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0092_modification_has_impact_loc'),
    ]

    operations = [
        migrations.AddField(
            model_name='componentcommit',
            name='commit_str',
            field=models.CharField(blank=True, default='', max_length=200, null=True),
        ),
    ]
