from django.utils import timezone
from django.db.models.aggregates import Sum
from django.contrib.auth.models import Group

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from accounts.models import UserAccount, Transaction, Currency, Wallet
from .serializers import TransactionSerializer


class TotalReport(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, **kwargs):
        # REGISTRATIONS
        registrations_total = UserAccount.objects.all().count()

        # PLAYERS
        players_total = Transaction.objects.filter(
            transaction_type='bet',
        ).order_by('user').distinct('user').count()

        # DEPOSITORS
        depositors_total = Transaction.objects.filter(
            transaction_type__contains='deposit',
            transaction_status='success',
        ).order_by('user').distinct('user').count()

        # DEPOSITS
        fiat_deposits_total = Transaction.objects.filter(
            transaction_type='deposit',
            transaction_status='success',
        ).aggregate(Sum('amount')).get('amount__sum') or 0

        # DEPOSIT_EXCHANGES
        crypto_deposit_total = Transaction.objects.filter(
            transaction_type='deposit_exchange',
            transaction_status='success',
        ).aggregate(Sum('amount')).get('amount__sum') or 0

        # AVERAGE DEPOSIT
        if registrations_total > 0:
            average_deposit_total = (fiat_deposits_total + crypto_deposit_total) / registrations_total
        else:
            average_deposit_total = 0

        return Response(data={
            'registration_total': registrations_total,
            'players_total': players_total,
            'depositors_total': depositors_total,
            'fiat_deposits_total': fiat_deposits_total,
            'crypto_deposit_exchange_total': crypto_deposit_total,
            'deposit_total': fiat_deposits_total + crypto_deposit_total,
            'average_deposit_total': average_deposit_total,
        }, status=status.HTTP_200_OK)


class MonthlyReport(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, **kwargs):
        today_date = timezone.now()
        prev_month_date = timezone.now().replace(day=1, hour=0, minute=0, second=1)

        # REGISTRATIONS
        registrations_current_month = UserAccount.objects.filter(
            registered_at__range=[prev_month_date, today_date]).count()

        # PLAYERS
        players_current_month = Transaction.objects.filter(
            transaction_type='bet',
            transaction_start_date__range=[prev_month_date, today_date]
        ).order_by('user').distinct('user').count()

        # DEPOSITORS
        depositors_current_month = Transaction.objects.filter(
            transaction_type__contains='deposit',
            transaction_status='success',
            transaction_start_date__range=[prev_month_date, today_date]
        ).order_by('user').distinct('user').count()

        # FIAT DEPOSITS
        fiat_deposits_current_month = Transaction.objects.filter(
            transaction_type='deposit',
            transaction_status='success',
            transaction_start_date__range=[prev_month_date, today_date]
        ).aggregate(Sum('amount')).get('amount__sum') or 0

        # CRYPTO DEPOSITS
        crypto_deposits_current_month = Transaction.objects.filter(
            transaction_type='deposit_exchange',
            transaction_status='success',
            transaction_start_date__range=[prev_month_date, today_date]
        ).aggregate(Sum('amount')).get('amount__sum') or 0

        # AVERAGE DEPOSIT
        if registrations_current_month > 0:
            average_deposit_current_month = (
                fiat_deposits_current_month + crypto_deposits_current_month) / registrations_current_month
        else:
            average_deposit_current_month = 0

        return Response(data={
            'from': prev_month_date.date(),
            'to': today_date.date(),
            'registration_current_month': registrations_current_month,
            'players_current_month': players_current_month,
            'depositors_current_month': depositors_current_month,
            'fiat_deposits_current_month': fiat_deposits_current_month,
            'crypto_deposits_current_month': crypto_deposits_current_month,
            'deposits_current_month': fiat_deposits_current_month + crypto_deposits_current_month,
            'average_deposit_current_month': average_deposit_current_month,
        }, status=status.HTTP_200_OK)


class DailyReport(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, **kwargs):
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

        # AVAREGE DEPOSIT
        if registrations_current_day > 0:
            average_deposit_current_day = (
                fiat_deposits_current_day + crypto_deposits_current_day) / registrations_current_day
        else:
            average_deposit_current_day = 0

        return Response(data={
            'from': yesterday_beginning,
            'to': yesterday_end,
            'registration_current_day': registrations_current_day,
            'players_current_day': players_current_day,
            'depositors_current_day': depositors_current_day,
            'fiat_deposits_current_day': fiat_deposits_current_day,
            'crypto_deposits_current_day': crypto_deposits_current_day,
            'deposits_current_day': fiat_deposits_current_day + crypto_deposits_current_day,
            'average_deposit_current_day': average_deposit_current_day,
        }, status=status.HTTP_200_OK)


class AdditionalReport(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, **kwargs):
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

        return Response(data={
            'real_balance': real_balance,
            'bonus_balance': bonus_balance,
        }, status=status.HTTP_200_OK)


class TransactionReport(APIView):
    permisssion_classes = [IsAuthenticated, IsAdminUser]

    def get(self, requests):
        transactions = Transaction.objects.all()
        serializer = TransactionSerializer(transactions, many=True)
        print(serializer)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
