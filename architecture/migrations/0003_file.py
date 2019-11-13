# Generated by Django 2.2.5 on 2019-11-12 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('architecture', '0002_compiled_previous_compiled'),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('directory', models.CharField(max_length=100)),
                ('has_compileds', models.BooleanField(default=False)),
            ],
        ),
    ]
