# Generated by Django 3.1.4 on 2021-06-30 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_transaction_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='city',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='country',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='zip',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
