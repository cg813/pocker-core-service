# Generated by Django 3.1.4 on 2021-10-05 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0004_auto_20210922_1559'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='is_test',
            field=models.BooleanField(default=False),
        ),
    ]
