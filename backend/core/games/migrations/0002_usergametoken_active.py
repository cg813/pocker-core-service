# Generated by Django 3.1.4 on 2021-06-15 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usergametoken',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
