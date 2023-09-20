from rest_framework import serializers
from .models import PaymentProvider, PaymentMethod
from accounts.models import Transaction


class PaymentMethodLSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentMethod
        fields = ('name', )


class PaymentProviderSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentProvider
        fields = ('id', 'name', 'website', 'merchant_number', 'gateway_number',
                  'testing', 'test_sign_key', 'test_endpoint', 'prod_sign_key',
                  'prod_endpoint', 'min_deposit', 'max_deposit',
                  'is_active', 'created_at')


class PaymentProviderListSerializer(serializers.ModelSerializer):
    methods = PaymentMethodLSerializer(source="payment_methods", many=True)

    class Meta:
        model = PaymentProvider
        fields = ('name', 'methods', 'regions')


class DepositSerializer(serializers.Serializer):
    provider = serializers.CharField(required=True)
    amount = serializers.FloatField(required=True)
    currency = serializers.CharField(required=True)


class WithdrawalSerializer(serializers.Serializer):
    amount = serializers.FloatField(required=True)
    card_number = serializers.CharField(required=True)
    card_month = serializers.CharField(required=True)
    card_year = serializers.CharField(required=True)
    card_holder = serializers.CharField(required=True)
    provider = serializers.CharField(required=True)


class OdeonpayWithdrawalSerializer(DepositSerializer):
    provider = serializers.CharField(required=True)
    amount = serializers.FloatField(required=True)
    currency = serializers.CharField(required=True)
    card_number = serializers.CharField(required=True)
    card_name = serializers.CharField(required=True)


class IBANWithdrawalSerializer(DepositSerializer):
    iban = serializers.CharField(required=True)
    swift = serializers.CharField(required=True)
    bank_address = serializers.CharField(required=True)


class UserWithdrawalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = ('transaction_id', 'amount', 'transaction_start_date')


class DixonPayDepositSerializer(serializers.Serializer):
    amount = serializers.CharField(required=True)
    currency = serializers.CharField(required=True)
    card_expire_month = serializers.CharField(required=True)
    card_expire_year = serializers.CharField(required=True)
    card_no = serializers.CharField(required=True)
    card_security_code = serializers.CharField(required=True)


class AlphapoDepositExchangeSerializer(serializers.Serializer):
    currency_from = serializers.ChoiceField(choices=['BTC', 'ETH', 'USD'])
    currency_to = serializers.ChoiceField(choices=['USD', 'BTC', 'ETH'])


class AlphapoWithdrawalExchangeSerializer(AlphapoDepositExchangeSerializer):
    address = serializers.CharField(required=True)
    amount = serializers.FloatField(required=True)


class TransactionHistoryRequestSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    stop_date = serializers.DateField(required=True)
    limit = serializers.IntegerField(required=True)
    page = serializers.IntegerField(required=True)
    type = serializers.CharField(required=True)


class TransactionHistorySerializer(serializers.ModelSerializer):

    currency = serializers.CharField(allow_null=True, source='currency.iso')
    payment_provider = serializers.CharField(allow_null=True, source='payment_provider.name')
    game = serializers.CharField(allow_null=True, source='game.name')

    class Meta:
        model = Transaction
        fields = ('amount', 'currency', 'transaction_start_date', 'transaction_end_date',
                  'transaction_status', 'game', 'game_round', 'balance', 'payment_provider',
                  'transaction_type')
