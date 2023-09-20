from django.utils import timezone
from rest_framework import status
from django.db import transaction

from games.models import UserGameToken
from accounts.models import Wallet, Transaction


class TransactionManager():

    def __init__(self, request_data):
        self.request_data = request_data
        self.amount = self.request_data.get('amount')
        self.transaction_type = self.request_data.get('transaction_type')
        self.token = None
        self.wallet = None

    def make_transaction(self):
        with transaction.atomic():
            self.token = UserGameToken.objects.get_or_none(token=self.request_data.get('token'), active=True)
            can_make_transaction, message = self.check_can_make_transaction()

            if can_make_transaction:
                print('TRANSACTION TYPE: ', self.transaction_type)
                self.create_transaction()

                message = {'status': 'Ok', 'total_balance': (self.wallet.balance + self.wallet.bonus_balance),
                           'currency': 'USD'}

        return status.HTTP_200_OK, message

    def check_can_make_transaction(self):
        if self.token:
            if self.request_data.get('transaction_type') in ['bet', 'win', 'reset', 'rollback']:
                self.wallet = Wallet.objects.select_for_update().get(user=self.token.user, active=True)
                self.check_for_bonus()

                if self.token.user.logged_out and self.request_data.get('transaction_type') == 'bet':
                    return False, {'status': 'Failed', 'error_description': 'user is logged out'}

                if self.check_if_requested_bet_is_less_than_balance():
                    return True, {'status': 'Ok'}

                return False, {'status': 'Failed', 'error_description': 'insufficient funds',
                               'total_balance': (self.wallet.balance + self.wallet.bonus_balance)}
            return False, {'status': 'Failed', 'error_description': 'unsupported operation'}
        return False, {'status': 'Failed', 'error_description': 'token is not valid'}

    def check_for_bonus(self):
        if self.wallet.bonus_expiration_date:
            if self.wallet.bonus_expiration_date < timezone.now():
                self.wallet.bonus_balance = 0
                self.wallet.bonus_bet = 0
                self.wallet.bonus_expiration_date = None
                self.wallet.bonus_requirement = None
                self.wallet.save()

    def check_if_requested_bet_is_less_than_balance(self):
        if self.transaction_type == 'bet' and self.amount > self.wallet.balance + self.wallet.bonus_balance:
            return False
        return True

    def create_transaction(self):
        handle_transaction = {
            'bet': self.handle_bet,
            'rollback': self.handle_rollback,
            'reset': self.handle_reset,
            'win': self.handle_win
        }.get(self.transaction_type)

        handle_transaction()

    def handle_bet(self):
        if self.amount <= self.wallet.bonus_balance:  # BONUS BET
            self.record_transaction(self.amount, self.wallet.bonus_balance, 'bonus_bet')
            self.update_wallet(self.amount, 'bonus_bet')

        elif self.wallet.bonus_balance == 0:  # REAL BET
            self.record_transaction(self.amount, self.wallet.balance, 'bet')
            self.update_wallet(self.amount, 'bet')

        elif self.amount > self.wallet.bonus_balance and self.wallet.bonus_balance > 0:  # COMBINED BET
            bonus_amount = self.wallet.bonus_balance
            real_amount = self.amount - self.wallet.bonus_balance

            self.record_transaction(bonus_amount, self.wallet.bonus_balance, 'bonus_bet')
            self.update_wallet(bonus_amount, 'bonus_bet')

            self.record_transaction(real_amount, self.wallet.balance, 'bet')
            self.update_wallet(real_amount, 'bet')

    def handle_rollback(self):
        if self.wallet.bonus_bet == 0:  # REAL MONEY ROLLBACK
            self.record_transaction(self.amount, self.wallet.balance, 'rollback')
            self.update_wallet(self.amount, 'rollback')
        else:
            if self.amount <= self.wallet.bonus_bet:  # BONUS ROLLBACK
                self.record_transaction(self.amount, self.wallet.balance, 'bonus_rollback')
                self.update_wallet(self.amount, 'bonus_rollback')
            elif self.amount > self.wallet.bonus_bet:  # COMBINED ROLLBACK
                bonus_amount = self.wallet.bonus_bet
                real_amount = self.amount - self.wallet.bonus_bet

                self.record_transaction(bonus_amount, self.wallet.bonus_balance, 'bonus_rollback')
                self.update_wallet(bonus_amount, 'bonus_rollback')

                self.record_transaction(real_amount, self.wallet.balance, 'rollback')
                self.update_wallet(real_amount, 'rollback')

    def handle_reset(self):
        if self.wallet.bonus_bet == 0:  # REAL MONEY RESET
            self.record_transaction(self.amount, self.wallet.balance, 'reset')
            self.update_wallet(self.amount, 'reset')

        else:
            if self.amount <= self.wallet.bonus_bet:  # BONUS RESET
                self.record_transaction(self.amount, self.wallet.bonus_balance, 'bonus_reset')
                self.update_wallet(self.amount, 'bonus_reset')

            elif self.amount > self.wallet.bonus_bet:  # COMBINED RESET
                bonus_amount = self.wallet.bonus_bet
                real_amount = self.amount - self.wallet.bonus_bet

                self.record_transaction(bonus_amount, self.wallet.bonus_balance, 'bonus_reset')
                self.update_wallet(bonus_amount, 'bonus_reset')

                self.record_transaction(real_amount, self.wallet.balance, 'reset')
                self.update_wallet(real_amount, 'reset')

    def handle_win(self):
        if self.wallet.bonus_bet == 0:  # REAL MONEY WIN
            self.record_transaction(self.amount, self.wallet.balance, 'win')
            self.update_wallet(self.amount, 'win')

        else:
            if self.amount == 0:  # COMBINED LOSE
                self.record_transaction(self.amount, self.wallet.bonus_balance, 'bonus_win')
                self.update_wallet(self.amount, 'bonus_win')
                self.record_transaction(self.amount, self.wallet.balance, 'win')

            elif self.amount <= self.wallet.bonus_bet:  # BONUS WIN
                self.record_transaction(self.amount, self.wallet.bonus_balance, 'bonus_win')
                self.update_wallet(self.amount, 'bonus_win')

            elif self.amount > self.wallet.bonus_bet:  # COMBINED WIN
                bonus_amount = self.wallet.bonus_bet
                real_amount = self.amount - self.wallet.bonus_bet

                self.record_transaction(bonus_amount, self.wallet.bonus_balance, 'bonus_win')
                self.update_wallet(bonus_amount, 'bonus_win')

                self.record_transaction(real_amount, self.wallet.balance, 'win')
                self.update_wallet(real_amount, 'win')

    def record_transaction(self, amount, balance, transaction_type):
        Transaction.objects.create(
            user=self.token.user,
            initial_amount=amount,
            amount=amount,
            transaction_end_date=timezone.now(),
            transaction_type=transaction_type,
            transaction_status='success',
            game=self.token.game,
            game_round=self.request_data.get('round_id'),
            game_transaction_id=self.request_data.get('external_id'),
            balance=balance
        )

    def update_wallet(self, amount, transaction_type):
        update_wallet_function = {
            'bet': self.subtract_from_balance,
            'win': self.add_to_balance,
            'reset': self.add_to_balance,
            'rollback': self.add_to_balance,
            'bonus_bet': self.subtract_from_bonus_balance,
            'bonus_win': self.add_to_bonus_balance,
            'bonus_reset': self.add_to_bonus_balance,
            'bonus_rollback': self.add_to_bonus_balance
        }.get(transaction_type)

        update_wallet_function(amount)

    def add_to_balance(self, amount):
        self.wallet.balance += amount
        self.wallet.save()

    def subtract_from_balance(self, amount):
        self.wallet.balance -= amount
        self.wallet.save()

    def add_to_bonus_balance(self, amount):
        self.wallet.bonus_balance += amount

        if self.transaction_type == 'win':
            self.wallet.bonus_bet = 0

        elif self.transaction_type == 'reset':
            self.wallet.bonus_bet = 0
            self.wallet.amount_wagered -= amount

        elif self.transaction_type == 'rollback':
            self.wallet.bonus_bet -= amount
            self.wallet.amount_wagered -= amount

        self.wallet.save()

    def subtract_from_bonus_balance(self, amount):
        self.wallet.bonus_balance -= amount
        self.wallet.amount_wagered += amount
        self.wallet.bonus_bet += amount
        self.wallet.save()
