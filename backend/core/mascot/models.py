from email.policy import default
from django.db import models
from uuid import uuid4

from accounts.models import UserAccount


class GetOrNoneManager(models.Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def first_or_none(self, **kwargs):
        try:
            return self.filter(**kwargs).first()
        except self.model.DoesNotExist:
            return None


class MascotBalanceLog(models.Model):
    callerId = models.IntegerField()
    playerName = models.CharField(max_length=50)
    initialBalance = models.IntegerField(default=0, null=True, blank=True)
    finalBalance = models.IntegerField(default=0, null=True, blank=True)
    withdraw = models.IntegerField(default=0, null=True, blank=True)
    deposit = models.IntegerField(default=0, null=True, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    transactionRef = models.CharField(max_length=100, null=True, blank=True)
    gameRoundRef = models.CharField(max_length=100, null=True, blank=True)
    gameId = models.CharField(max_length=100, null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    reason = models.CharField(max_length=100, null=True, blank=True)
    sessionId = models.CharField(max_length=100, null=True, blank=True)
    sessionAlternativeId = models.CharField(
        max_length=100, null=True, blank=True)
    spinDetails = models.CharField(max_length=100, null=True, blank=True)
    bonusId = models.CharField(max_length=100, null=True, blank=True)
    chargeFreerounds = models.CharField(max_length=100, null=True, blank=True)
    transactionId = models.UUIDField(default=uuid4)
    description = models.CharField(max_length=250, null=True, blank=True)
    real_amount = models.IntegerField(default=0, null=True, blank=True)
    bonus_amount = models.IntegerField(default=0, null=True, blank=True)

    objects = GetOrNoneManager()

    def __str__(self):
        return str(self.transactionId)


class MascotBanks(models.Model):
    name = models.CharField(max_length=100, default='main_usd_bank')
    currency = models.CharField(max_length=3, default='USD')
    is_default = models.BooleanField(default=False)

    objects = GetOrNoneManager()

    def __str__(self):
        return self.name + self.currency


class MascotPlayerBanks(models.Model):
    player_id = models.ForeignKey(
        'accounts.UserAccount', on_delete=models.CASCADE)
    bank_id = models.ForeignKey('mascot.MascotBanks', on_delete=models.CASCADE)
    objects = GetOrNoneManager()


class MascotSessions(models.Model):

    game_types = [
        ('with bonus', 'with bonus'),
        ('only bonus', 'only bonus'),
        ('without bonus', 'without bonus')
    ]
    session_id = models.CharField(max_length=100)
    type = models.CharField(
        max_length=20,
        choices=game_types
    )

    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
