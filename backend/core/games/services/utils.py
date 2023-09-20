from django.utils import timezone

from accounts.models import Wallet


def get_balance(wallet: Wallet):
    if wallet.bonus_expiration_date:
        if wallet.bonus_expiration_date > timezone.now():
            return (wallet.balance + wallet.bonus_balance)
        else:
            wallet.bonus_balance = 0
            wallet.bonus_bet = 0
            wallet.bonus_expiration_date = None
            wallet.bonus_requirement = None
            wallet.save()
    return wallet.balance
