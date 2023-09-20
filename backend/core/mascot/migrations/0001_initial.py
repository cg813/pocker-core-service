# Generated by Django 3.1.4 on 2022-02-14 13:27

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MascotBalanceLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('callerId', models.IntegerField()),
                ('playerName', models.CharField(max_length=50)),
                ('initialBalance', models.IntegerField(blank=True, default=0, null=True)),
                ('finalBalance', models.IntegerField(blank=True, default=0, null=True)),
                ('withdraw', models.IntegerField(blank=True, default=0, null=True)),
                ('deposit', models.IntegerField(blank=True, default=0, null=True)),
                ('currency', models.IntegerField(default=0)),
                ('transactionRef', models.CharField(blank=True, max_length=100, null=True)),
                ('gameRoundRef', models.CharField(blank=True, max_length=100, null=True)),
                ('gameId', models.CharField(blank=True, max_length=100, null=True)),
                ('source', models.CharField(blank=True, max_length=100, null=True)),
                ('reason', models.CharField(blank=True, max_length=100, null=True)),
                ('sessionId', models.CharField(blank=True, max_length=100, null=True)),
                ('sessionAlternativeId', models.CharField(blank=True, max_length=100, null=True)),
                ('spinDetails', models.CharField(blank=True, max_length=100, null=True)),
                ('bonusId', models.CharField(blank=True, max_length=100, null=True)),
                ('chargeFreerounds', models.CharField(blank=True, max_length=100, null=True)),
                ('transactionId', models.UUIDField(default=uuid.uuid4)),
                ('description', models.CharField(blank=True, max_length=250, null=True)),
            ],
        ),
    ]
