# Generated by Django 3.1.4 on 2022-03-27 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0030_auto_20220120_1408'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallet',
            name='free_spin',
            field=models.IntegerField(default=0),
        ),
    ]
