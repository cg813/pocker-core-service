# Generated by Django 3.1.4 on 2021-08-10 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0002_usergametoken_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='game_id',
            field=models.CharField(max_length=200),
        ),
    ]
