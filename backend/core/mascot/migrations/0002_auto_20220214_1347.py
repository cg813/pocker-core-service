# Generated by Django 3.1.4 on 2022-02-14 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mascot', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mascotbalancelog',
            name='currency',
            field=models.CharField(default='USD', max_length=10),
        ),
    ]
