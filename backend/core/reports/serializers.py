from rest_framework import serializers
from accounts.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['transaction_id', 'user', 'amount', 'currency', 'transaction_start_date',
                  'transaction_end_date', 'transaction_type', 'transaction_status', 'game',
                  'game_round', 'balance']
