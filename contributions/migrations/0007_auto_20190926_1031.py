# Generated by Django 2.2.5 on 2019-09-26 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0006_auto_20190926_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modification',
            name='added',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='modification',
            name='complexity',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='modification',
            name='new_path',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='modification',
            name='nloc',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='modification',
            name='removed',
            field=models.IntegerField(null=True),
        ),
    ]
