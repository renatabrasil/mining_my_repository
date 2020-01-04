# Generated by Django 3.0 on 2020-01-04 00:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0033_auto_20200103_2121'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modification',
            name='file_by_author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='modifications', to='contributions.FileByAuthor'),
        ),
    ]
