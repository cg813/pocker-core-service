
from locale import currency
from django.utils import timezone
from accounts.models import Currency
from mascot.models import MascotBalanceLog
from mascot.serializers import MascotBalanceLogSerializer

from games.models import Game
from accounts.models import UserAccount
from accounts.models import Transaction


class MascotTransactionsManager():
    def __init__(self, request_data):
        self.game_id = request_data.get('game_id')
        self.user_id = request_data.get('user_id')

        if self.game_id != 'N/A':
            self.game = Game.objects.first_or_none(game_id=self.game_id)
        else:
            self.game = None

        self.user = UserAccount.objects.first_or_none(id=self.user_id)
        self.request_data = request_data
        self.currancy = Currency.objects.filter(iso="USD").first()

    def handle_withdraw_request(self):
        self.record_transactions('bet')

    def handle_deposit_request(self):
        self.record_transactions('win')

    def record_transactions(self, transaction_type):

        Transaction.objects.create(
            user=self.user,
            initial_amount=self.request_data.get('amount'),
            amount=self.request_data.get('amount'),
            transaction_end_date=timezone.now(),
            transaction_type=transaction_type,
            transaction_status='success',
            game=self.game,
            game_round=self.request_data.get('round_id'),
            game_transaction_id=self.request_data.get('external_id'),
            balance=self.request_data.get('final_balance'),
            currency=self.currancy
        )


class MascotUserBalanceChange():
    def change_balance(self, type, balance_type, amount, wallet, user_id):
        if balance_type == 'with bonus':
            if type == 'deposit':
                last_mascot_log = MascotBalanceLog.objects.filter(
                    playerName=user_id).last()
                last_mascot_log_serialize = MascotBalanceLogSerializer(
                    last_mascot_log)
                if last_mascot_log_serialize.data['real_amount'] != 0:
                    wallet.balance += amount
                    wallet.balance = round(wallet.balance, 3)
                    wallet.save()
                    real_amount = amount
                    bonus_amount = 0
                else:
                    wallet.bonus_balance += amount
                    wallet.bonus_balance = round(wallet.bonus_balance, 3)
                    wallet.save()
                    real_amount = 0
                    bonus_amount = amount
            elif type == 'withdraw':
                if wallet.bonus_balance > 0:
                    if wallet.bonus_balance >= amount:
                        wallet.bonus_balance -= amount
                        wallet.bonus_balance = round(wallet.bonus_balance, 3)
                        wallet.amount_wagered += amount
                        wallet.amount_wagered = round(wallet.amount_wagered, 3)
                        wallet.save()
                        real_amount = 0
                        bonus_amount = amount
                    if wallet.bonus_balance < amount:

                        remain_amount = amount - wallet.bonus_balance
                        real_amount = remain_amount
                        bonus_amount = wallet.bonus_balance
                        wallet.amount_wagered += wallet.bonus_balance
                        wallet.amount_wagered = round(wallet.amount_wagered, 3)
                        wallet.bonus_balance = 0
                        wallet.bonus_balance = round(wallet.bonus_balance, 3)
                        wallet.balance - remain_amount
                        wallet.save()
                else:
                    wallet.balance -= amount
                    wallet.balance = round(wallet.balance, 3)
                    wallet.save()
                    real_amount = amount
                    bonus_amount = 0
        elif balance_type == 'without bonus':
            if type == 'deposit':
                wallet.balance += amount
                wallet.balance = round(wallet.balance, 3)
                wallet.save()
                real_amount = amount
                bonus_amount = 0
            elif type == 'withdraw':
                wallet.balance -= amount
                wallet.balance = round(wallet.balance, 3)
                wallet.save()
                real_amount = amount
                bonus_amount = 0
        elif balance_type == 'only bonus':
            if type == 'deposit':
                wallet.bonus_balance += amount
                wallet.bonus_balance = round(wallet.bonus_balance, 3)
                wallet.save()
                real_amount = 0
                bonus_amount = amount
            elif type == 'withdraw':
                wallet.bonus_balance -= amount
                wallet.bonus_balance = round(wallet.bonus_balance, 3)
                wallet.amount_wagered += amount
                wallet.amount_wagered = round(wallet.amount_wagered, 3)
                wallet.save()
                real_amount = 0
                bonus_amount = amount

        return real_amount, bonus_amount
