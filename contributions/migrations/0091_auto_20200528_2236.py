# Generated by Django 3.0 on 2020-05-29 01:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contributions', '0090_auto_20200525_2234'),
    ]

    operations = [
        migrations.AddField(
            model_name='commit',
            name='real_tag_description',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='real_tag_description',
            field=models.CharField(default='', max_length=100),
        ),
    ]
