from celery import shared_task
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.models import Group

from accounts.models import UserAccount, Transaction, Currency, Wallet, Rate
from .models import DailyReport


@shared_task
def daily_report_task():
    yesterday_beginning = (timezone.now() - timezone.timedelta(1)).replace(hour=0, minute=0, second=1)
    yesterday_end = (timezone.now() - timezone.timedelta(1)).replace(hour=23, minute=59, second=59)
    print(yesterday_beginning)
    print(yesterday_end)

    # REGISTRATIONS
    registrations_current_day = UserAccount.objects.filter(
        registered_at__range=[yesterday_beginning, yesterday_end]).count()

    # PLAYERS
    players_current_day = Transaction.objects.filter(
        transaction_type='bet',
        transaction_start_date__range=[yesterday_beginning, yesterday_end]
    ).order_by('user').distinct('user').count()

    # DEPOSITORS
    depositors_current_day = Transaction.objects.filter(
        transaction_type__contains='deposit',
        transaction_status='success',
        transaction_start_date__range=[yesterday_beginning, yesterday_end]
    ).order_by('user').distinct('user').count()

    # FIAT DEPOSITS
    fiat_deposits_current_day = Transaction.objects.filter(
        transaction_type='deposit',
        transaction_status='success',
        transaction_start_date__range=[yesterday_beginning, yesterday_end]
    ).aggregate(Sum('amount')).get('amount__sum') or 0

    # CRYPTO DEPOSITS
    crypto_deposits_current_day = Transaction.objects.filter(
        transaction_type='deposit_exchange',
        transaction_status='success',
        transaction_start_date__range=[yesterday_beginning, yesterday_end]
    ).aggregate(Sum('amount')).get('amount__sum') or 0

    # AVERAGE DEPOSIT
    if registrations_current_day > 0:
        average_deposit_current_day = (fiat_deposits_current_day
                                       + crypto_deposits_current_day) / registrations_current_day
    else:
        average_deposit_current_day = 0

    # ADDITIONAL REPORT
    currency = Currency.objects.get(iso='USD')

    groups = ['MONITORING', 'TESTPLAYER']
    groups = Group.objects.filter(name__in=groups)

    exclude_list = UserAccount.objects.filter(groups__in=groups)
    exclude_list = list(filter((None).__ne__, exclude_list))

    # DEPOSITS
    real_balance = Wallet.objects.filter(
        currency=currency,
    ).exclude(user__in=exclude_list).aggregate(Sum('balance')).get('balance__sum')

    bonus_balance = Wallet.objects.filter(
        currency=currency,
    ).exclude(user__in=exclude_list).aggregate(Sum('bonus_balance')).get('bonus_balance__sum')

    data = {
        'from': yesterday_beginning,
        'to': yesterday_end,
        'registration_current_day': registrations_current_day,
        'players_current_day': players_current_day,
        'depositors_current_day': depositors_current_day,
        'fiat_deposits_current_day': fiat_deposits_current_day,
        'crypto_deposits_current_day': crypto_deposits_current_day,
        'deposits_current_day': fiat_deposits_current_day + crypto_deposits_current_day,
        'average_deposit_current_day': average_deposit_current_day,
        'real_balance': real_balance,
        'bonus_balance': bonus_balance
    }
    print('REPORT CREATED', data)

    DailyReport.objects.create(
        report_from=yesterday_beginning,
        report_to=yesterday_end,
        registrations=registrations_current_day,
        players=players_current_day,
        depositors=depositors_current_day,
        fiat_deposits=fiat_deposits_current_day,
        crypto_deposits=crypto_deposits_current_day,
        total_deposits=fiat_deposits_current_day+crypto_deposits_current_day,
        average_deposits=average_deposit_current_day,
        real_balance_total=real_balance,
        bonus_balance_total=bonus_balance
    )

@shared_task
def get_daily_currency_task():
    import requests
    response = requests.get("https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/ka/json")
    print(response.text)
    eur_rate = 0.0
    usd_rate = 0.0
    if response.status_code == 200:
        response = response.json()
        for data in response:
            currencies = data["currencies"]
            for currencyData in currencies:
                if currencyData["code"] == "EUR":
                    eur_rate = currencyData["rate"] / currencyData["quantity"]
                if currencyData["code"] == "USD":
                    usd_rate = currencyData["rate"] / currencyData["quantity"]
                if currencyData["code"] == "RUB":
                    rub_rate = currencyData["rate"] / currencyData["quantity"]
    else:
        response = response.json()
        print(response, "bad request ")
    usd_to_eur = usd_rate / eur_rate

    Rate.objects.create(
        currency_from=Currency.objects.get_or_none(iso='USD'),
        currency_to_string="EUR",
        rate=usd_to_eur,
    )

    eur_to_usd = eur_rate / usd_rate
    Rate.objects.create(
        currency_from=Currency.objects.get_or_none(iso='EUR'),
        currency_to_string="USD",
        rate=eur_to_usd,
    )

    usd_to_rub = usd_rate / rub_rate
    Rate.objects.create(
        currency_from=Currency.objects.get_or_none(iso='USD'),
        currency_to_string="RUB",
        rate=usd_to_rub,
    )


