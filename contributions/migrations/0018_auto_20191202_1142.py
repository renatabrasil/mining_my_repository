# Generated by Django 2.2.5 on 2019-12-02 14:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0017_auto_20191122_1302'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Method',
        ),
        migrations.RemoveField(
            model_name='commit',
            name='project',
        ),
    ]