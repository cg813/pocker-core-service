import requests
from uuid import uuid4
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager)

from django.utils import timezone
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from bonus.models import Bonus


class GetOrNoneManager(models.Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class UserAccountManager(BaseUserManager):
    """ Create manager for our custom user table """

    def create_user(self, username: str, email: str, password: str, birth_date: str = '2000-01-01', **kwargs):
        """ Method for creating users and saving user objects to database """
        if not email:
            raise ValueError("user must have email")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email,
                          birth_date=birth_date, registered_at=timezone.now())
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username: str, email: str,  password: str):
        """ Method for creating super user with all the permissions """
        user = self.create_user(
            username=username, email=email, password=password)
        user.is_active = True
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user

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


class UserAccount(AbstractBaseUser, PermissionsMixin):
    """ Custom user model  """
    first_name = models.CharField(max_length=128, null=True, blank=True)
    last_name = models.CharField(max_length=128, null=True, blank=True)
    username = models.CharField(max_length=128)
    email = models.EmailField(max_length=128, unique=True)
    birth_date = models.DateField(null=True, blank=True,)
    gender_choices = [
        ('male', 'male'),
        ('female', 'female'),
        ('other', 'other')
    ]
    gender = models.CharField(
        max_length=100,
        choices=gender_choices,
        null=True, blank=True
    )
    identification_number = models.CharField(
        max_length=250, null=True, blank=True)
    user_id = models.CharField(max_length=20, null=True, blank=True)

    country = models.CharField(max_length=250, null=True, blank=True)
    city = models.CharField(max_length=250, null=True, blank=True)
    zip = models.CharField(max_length=250, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    is_pep = models.BooleanField(default=False)

    is_dealer = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    registered_at = models.DateTimeField(null=True, blank=True)
    logged_out = models.BooleanField(default=False)

    verification_status_choices = [
        ('unverified', 'unverified'),
        ('pending', 'pending'),
        ('verified', 'verified'),
        ('rejected', 'rejected'),
    ]
    verification_status = models.CharField(
        max_length=100,
        choices=verification_status_choices,
        default='unverified'
    )

    identification_document_1 = models.CharField(max_length=500, null=True, blank=True)
    identification_document_2 = models.CharField(max_length=500, null=True, blank=True)

    BTC_TO_USD = models.CharField(max_length=500, null=True, blank=True)
    ETH_TO_USD = models.CharField(max_length=500, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', ]

    objects = UserAccountManager()

    def __str__(self):
        return self.email


@receiver(post_save, sender=UserAccount)
def create_wallets(sender, instance, created, **kwargs):
    if created is True:
        currencies = Currency.objects.all()
        bonus = Bonus.objects.filter(
            active_to__gt=timezone.now(), is_deposit_bonus=False).first()

        bonus_data = {}
        if bonus:
            bonus_data['bonus_balance'] = bonus.amount
            bonus_data['bonus_expiration_date'] = timezone.now(
            ) + timedelta(days=bonus.expiration_time_days)
            bonus_data['bonus_requirement'] = bonus
            bonus_data['notify_bonus'] = True

        for currency in currencies:
            active = False
            if currency.is_main is True:
                active = True

            Wallet.objects.create(
                user=instance,
                currency=currency,
                balance=0,
                active=active,
                **bonus_data if currency.iso == 'USD' else {}  # only for USD
            )


@receiver(pre_save, sender=UserAccount)
def handle_identity_verification(sender, instance, **kwargs):
    """ HERE WE SEND A NOTIFYING EMAIL REGARDING THE VERIFICATION TO THE USER """

    if instance.id:
        current = instance
        previous = UserAccount.objects.get(id=instance.id)

        if previous.verification_status == 'pending' and current.verification_status in ['verified', 'rejected']:
            from .tasks import send_identity_verification_email

            send_identity_verification_email(current)


class Currency(models.Model):
    """ CUSTOM CURRENCY TABLE """
    iso = models.CharField(max_length=50)
    symbol = models.CharField(max_length=50)
    full_name = models.CharField(max_length=500)

    is_crypto = models.BooleanField(default=False)
    divider = models.FloatField(default=1)
    parent_currency = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_main = models.BooleanField(default=False)

    objects = GetOrNoneManager()

    def __str__(self):
        return self.iso


@receiver(post_save, sender=Currency)
def create_wallets_on_new_currency_creation(sender, instance,
                                            created, **kwargs):
    if created is True:
        users = UserAccount.objects.all()

        active = False
        if instance.is_main:
            active = True

        for user in users:
            Wallet.objects.create(
                user=user,
                currency=instance,
                active=active
            )


# @receiver(post_save, sender=Currency)
def create_rates_on_new_currency_creation(sender, instance, created, **kwargs):
    if created:
        currencies = Currency.objects.all()

        forward_data = requests.get(
            f'https://api.exchangerate-api.com/v4/latest/{instance.iso}')
        forward_rates = forward_data.json().get('rates')

        for currency in currencies:
            if currency != instance:
                Rate.objects.create(
                    currency_from=instance,
                    currency_to=currency,
                    rate=forward_rates.get(currency.iso),
                )

                backward_data = requests.get(
                    f'https://api.exchangerate-api.com/v4/latest/{currency.iso}')
                backward_rates = backward_data.json().get('rates')

                Rate.objects.create(
                    currency_from=currency,
                    currency_to=instance,
                    rate=backward_rates.get(instance.iso),
                )


class Rate(models.Model):
    """ CUSTOM RATE TABLE """
    currency_from = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='currency_from'
    )
    currency_to = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='currency_to'
    )

    currency_to_string = models.CharField(
        max_length=100, null=True, blank=True)

    rate = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.currency_to is None:
            return f'''from {self.currency_from} to {self.currency_to_string}
                                at {self.created_at}'''
        else:
            return f'''from {self.currency_from} to {self.currency_to}
                                            at {self.created_at}'''


class Wallet(models.Model):
    """ CUSTOM WALLET MODEL """
    user = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    balance = models.FloatField(default=0)

    bonus_balance = models.FloatField(default=0)
    bonus_bet = models.FloatField(default=0)
    amount_wagered = models.FloatField(default=0)
    free_spin = models.IntegerField(default=0)
    bonus_expiration_date = models.DateTimeField(null=True, blank=True)
    bonus_requirement = models.ForeignKey(
        Bonus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    notify_bonus = models.BooleanField(default=False)

    active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = GetOrNoneManager()

    def __str__(self):
        if user := self.user:
            return f"{user.email}'s {self.currency} wallet"
        return f"Unknown user's {self.currency} wallet"


class Transaction(models.Model):
    """ CUSTOM TRANSACTION TABLE """
    transaction_id = models.UUIDField(default=uuid4)
    user = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    transaction_token = models.CharField(max_length=200, null=True, blank=True)

    initial_amount = models.FloatField()
    amount = models.FloatField()
    currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    rate = models.FloatField(null=True, blank=True)
    fee = models.FloatField(null=True, blank=True)

    transaction_start_date = models.DateTimeField(null=True, blank=True)
    transaction_end_date = models.DateTimeField(null=True, blank=True)

    transaction_type_choices = [
        ('deposit', 'deposit'),
        ('deposit_exchange', 'deposit_exchange'),
        ('withdrawal', 'withdrawal'),
        ('withdrawal_exchange', 'withdrawal_exchange'),
        ('bet', 'bet'),
        ('win', 'win'),
        ('reset', 'reset'),
        ('rollback', 'rollback'),
        ('bonus_bet', 'bonus_bet'),
        ('bonus_win', 'bonus_win'),
        ('bonus_reset', 'bonus_reset'),
        ('bonus_rollback', 'bonus_rollback'),
        ('refund', 'refund'),
    ]
    transaction_type = models.CharField(
        max_length=100,
        choices=transaction_type_choices,
    )

    transaction_status_choices = [
        ('pending', 'pending'),
        ('manual_confirmation', 'manual_confirmation'),
        ('waiting_for_provider_confirmation', 'waiting_for_provider_confirmation'),
        ('success', 'success'),
        ('deleted', 'deleted'),
    ]
    transaction_status = models.CharField(
        max_length=100,
        choices=transaction_status_choices
    )

    transaction_order_number = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        unique=True
    )

    game = models.ForeignKey(
        'games.Game',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    game_round = models.CharField(max_length=200, null=True, blank=True)
    game_transaction_id = models.UUIDField(null=True, blank=True)

    balance = models.FloatField()

    description = models.TextField(null=True, blank=True)

    details = models.JSONField(null=True, blank=True)

    payment_provider = models.ForeignKey(
        'payments.PaymentProvider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    objects = GetOrNoneManager()

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.transaction_start_date = timezone.now()
        super(Transaction, self).save(*args, **kwargs)

    def __str__(self):
        return f'''{self.user} - {self.transaction_type}: {self.initial_amount} {self.currency if self.currency else ''} -
                   {self.transaction_status} - {self.transaction_start_date} -
                   {self.transaction_id} - {self.transaction_order_number if self.transaction_order_number else ''}'''


@receiver(pre_save, sender=Transaction)
def handle_transaction_confirmations(sender, instance, **kwargs):
    if instance.id:  # if transaction was not created
        current = instance
        previous = Transaction.objects.get(id=instance.id)

        # HANDLE WITHDRAWALS
        if current.transaction_type in ['withdrawal', 'withdrawal_exchange']:

            # HANDLE TRANSACTION DELETION
            if previous.transaction_status == 'pending' and current.transaction_status == 'deleted':

                wallet = Wallet.objects.get(
                    user=current.user, currency__iso='USD')
                if current.transaction_type == 'withdrawal':
                    wallet.balance += current.amount
                elif current.transaction_type == 'withdrawal_exchange':
                    wallet.balance += current.initial_amount
                wallet.save()

            # HANDLE TRANSACTION MANUAL CONFIRMATION
            if previous.transaction_status == 'pending' and current.transaction_status == 'manual_confirmation':

                # INTERKASSA
                if current.payment_provider.name == 'interkassa':
                    from payments.services.payment_endpoints import make_interkassa_withdrawal
                    make_interkassa_withdrawal(current)
                # ODEONPAY
                if current.payment_provider.name == 'odeonpay':
                    from payments.services.payment_endpoints import make_odeonpay_withdrawal
                    make_odeonpay_withdrawal(current)

                # ALPHAPO
                if current.payment_provider.name == 'alphapo':
                    from payments.services.payment_endpoints import make_alphapo_withdrawal_exchange
                    make_alphapo_withdrawal_exchange(current)

        # HANDLE DEPOSITS
        if current.transaction_type in ['deposit', 'deposit_exchange']:
            if current.transaction_status == 'success' and previous.transaction_status != 'success':
                bonus = Bonus.objects.get_or_none(
                    is_deposit_bonus=True, active_to__gt=timezone.now())
                if bonus and current.amount >= bonus.deposit_amount:
                    wallet = Wallet.objects.get_or_none(
                        user=current.user, active=True)
                    wallet.bonus_balance = bonus.amount
                    wallet.bonus_expiration_date = timezone.now(
                    ) + timezone.timedelta(days=bonus.expiration_time_days)
                    wallet.bonus_requirement = bonus
                    wallet.save()
                    print(f'BONUS WAS ADDED TO {wallet}')
