# Generated by Django 3.1.4 on 2022-01-13 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0006_auto_20211230_0851'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentprovider',
            name='withdrawal',
            field=models.BooleanField(default=False),
        ),
    ]
