# Generated by Django 3.0 on 2020-04-23 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataanalysis', '0005_auto_20200217_1657'),
    ]

    operations = [
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
                'managed': False,
            },
        ),
    ]