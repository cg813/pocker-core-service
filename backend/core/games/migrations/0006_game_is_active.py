# Generated by Django 3.1.4 on 2021-10-10 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0005_game_is_test'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
