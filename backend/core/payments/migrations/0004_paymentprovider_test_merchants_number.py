# Generated by Django 3.1.4 on 2021-11-04 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_auto_20210831_0810'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentprovider',
            name='test_merchants_number',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
