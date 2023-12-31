# Generated by Django 3.1.4 on 2021-06-02 07:46

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_useraccount_is_dealer'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='address',
            field=models.CharField(default='wwww', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='useraccount',
            name='birth_date',
            field=models.DateField(default=datetime.datetime(2021, 6, 2, 7, 46, 32, 108967, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='useraccount',
            name='phone_number',
            field=models.CharField(default='59980683', max_length=15),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='useraccount',
            name='user_id',
            field=models.CharField(default=12345678909, max_length=20),
            preserve_default=False,
        ),
    ]
