from django.db import models


class GetOrNoneManager(models.Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class DailyReport(models.Model):
    """ CUSTOM DAILYREPORT MODEL """
    report_from = models.DateTimeField()
    report_to = models.DateTimeField()

    registrations = models.IntegerField(default=0)
    players = models.IntegerField(default=0)
    depositors = models.IntegerField(default=0)
    fiat_deposits = models.FloatField(default=0)
    crypto_deposits = models.FloatField(default=0)
    total_deposits = models.FloatField(default=0)
    average_deposits = models.FloatField(default=0)

    real_balance_total = models.FloatField(default=0)
    bonus_balance_total = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now=True)

    objects = GetOrNoneManager()

    def __str__(self):
        return f'{self.report_from.date()}'
