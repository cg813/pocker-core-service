from django.db import models
from django.utils import timezone


class GetOrNoneManager(models.Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class Bonus(models.Model):
    name = models.CharField(max_length=250)
    amount = models.IntegerField()
    wager_number = models.IntegerField()

    active_from = models.DateTimeField()
    active_to = models.DateTimeField()
    expiration_time_days = models.IntegerField()

    games = models.ForeignKey(
        'games.Game',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_deposit_bonus = models.BooleanField(default=False)
    deposit_amount = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = GetOrNoneManager()

    def __str__(self):
        return f"{self.name}, {'expired' if self.active_to < timezone.now() else 'active'}"
