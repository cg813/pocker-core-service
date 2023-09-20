from django.db import models


class GetOrNoneManager(models.Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class PaymentMethod(models.Model):
    name = models.CharField(max_length=250)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PaymentProvider(models.Model):
    name = models.CharField(max_length=250)
    website = models.URLField(null=True, blank=True)

    gateway_number = models.CharField(max_length=250, null=True, blank=True)

    merchant_number = models.CharField(max_length=250, null=True, blank=True)
    prod_sign_key = models.CharField(max_length=250, null=True, blank=True)
    prod_endpoint = models.URLField(null=True, blank=True)

    testing = models.BooleanField(default=True)
    test_merchant_number = models.CharField(max_length=250, null=True, blank=True)
    test_sign_key = models.CharField(max_length=250, null=True, blank=True)
    test_endpoint = models.URLField(null=True, blank=True)

    min_deposit = models.FloatField(null=True, blank=True)
    max_deposit = models.FloatField(null=True, blank=True)

    payment_methods = models.ManyToManyField(PaymentMethod)

    is_active = models.BooleanField(default=True)
    is_crypto = models.BooleanField(default=0)
    regions = models.CharField(null=True, blank=True, max_length=500)

    withdrawal = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = GetOrNoneManager()

    def __str__(self):
        return self.name
