# Generated by Django 3.1.4 on 2021-11-21 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0022_auto_20211115_1035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_order_number',
            field=models.CharField(blank=True, max_length=200, null=True, unique=True),
        ),
    ]
