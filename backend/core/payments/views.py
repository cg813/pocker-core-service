import requests
import hashlib
import json
from builtins import Exception
from uuid import UUID

from django.shortcuts import redirect
from django.utils import timezone
from django.db.utils import IntegrityError
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from uuid import uuid4


from .models import PaymentMethod, PaymentProvider
from accounts.models import Transaction, UserAccount, Currency, Wallet
from .serializers import (DepositSerializer, IBANWithdrawalSerializer, PaymentProviderListSerializer,
                          WithdrawalSerializer, PaymentMethodLSerializer, UserWithdrawalSerializer,
                          DixonPayDepositSerializer, AlphapoDepositExchangeSerializer,
                          AlphapoWithdrawalExchangeSerializer, TransactionHistoryRequestSerializer,
                          TransactionHistorySerializer, OdeonpayWithdrawalSerializer)

from .permissions import (AlphaPoCallbackPermission, DixonPayCallbackPermission, InterkassaCallbackPermission,
                          WonderlandPayCallbackPermission, EnsopayCallbackPermission, OdeonpayCallbackPermission,
                          SyspayCallbackPermission, FintechCashierCallbackPermission, CertusCallbackPermission)
from .tasks import s2s_send_transaction
from .services.utils import take_user_ip, get_currency
from .services.psp.alphapo import generate_alphapo_exchange_address
from .services.payment_endpoints import get_min_deposit
from .services.psp.wonderlandpay import get_wonderlandpay_redirect_url
from .services.psp.interkassa import get_interkassa_redirect_url
from .services.psp.ensopay import get_ensopay_redirect_url
from .services.psp.fintech_cashier import get_fintech_cashier_redirect_url
from .services.psp.neobanq import get_neobanq_redirect_url
from .services.psp.odeonpay import get_odeonpay_redirect_url
from .services.psp.syspay import get_syspay_redirect_url
from .services.psp.payecards import get_payecards_redirect_url
from .services.psp.certus import get_certus_redirect_url


class PaymentMethodView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, requst, **kwargs):
        methods = PaymentMethod.objects.filter(is_active=True)

        serializer = PaymentMethodLSerializer(methods, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class AlphapoDepositExchangeAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        serializer = AlphapoDepositExchangeSerializer(data=request.query_params)

        if serializer.is_valid():
            user = UserAccount.objects.get_or_none(pk=request.user.pk)
            attirbute_name = f'{serializer.data.get("currency_from")}_TO_{serializer.data.get("currency_to")}'

            address = getattr(user, attirbute_name)

            if not address:
                address = generate_alphapo_exchange_address(user, serializer.data.get('currency_from'),
                                                            serializer.data.get('currency_to'))
                setattr(
                    user, f"{serializer.data.get('currency_from')}_TO_{serializer.data.get('currency_to')}",
                    address)
                user.save()

            return Response(data={
                'address': address,
                'currency_from': serializer.data.get('currency_from'),
                'currency_to': serializer.data.get('currency_to')
            }, status=status.HTTP_200_OK)

        return Response(data={
            "message": 'invalid parameters'
        }, status=status.HTTP_400_BAD_REQUEST)


class AlphapoWithdrawalExchangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        serializer = AlphapoWithdrawalExchangeSerializer(data=request.data)

        if serializer.is_valid():
            user = UserAccount.objects.get_or_none(pk=request.user.pk)
            currency = Currency.objects.get_or_none(iso=serializer.data.get('currency_from'))
            wallet = Wallet.objects.get_or_none(user=user, currency=currency)
            provider = PaymentProvider.objects.get_or_none(name='alphapo')

            # IF USER HAS INSUFFICIENT FUNDS
            if serializer.data.get('amount') > wallet.balance:
                return Response(
                    data={
                        'message': 'Insufficient funds',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            transaction_id = uuid4()

            Transaction.objects.create(
                transaction_id=transaction_id,
                user=user,
                initial_amount=serializer.data.get('amount'),
                amount=0,
                currency=currency,
                transaction_type='withdrawal_exchange',
                transaction_status='pending',
                balance=wallet.balance,
                payment_provider=provider,
                details=serializer.data
            )

            # DEDUCT THE AMOUNT FROM THE WALLET
            wallet.balance -= float(serializer.data.get('amount'))
            wallet.save()

            return Response(data={
                'message': 'transaction was created',
                'balance': wallet.balance
            }, status=status.HTTP_201_CREATED)

        return Response(data={
            'message': 'invalid data'
        }, status=status.HTTP_400_BAD_REQUEST)


class AlphapoPaymentSpecificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        serializer = AlphapoDepositExchangeSerializer(data=request.query_params)

        if serializer.is_valid():
            user = UserAccount.objects.get(pk=request.user.pk)

            min_deposit, rate = get_min_deposit(user, serializer.data.get('currency_from'),
                                                serializer.data.get('currency_to'))

            return Response(data={
                'min_deposit': min_deposit,
                'rate': rate
            }, status=status.HTTP_200_OK)

        return Response(data={
            'message': 'invalid parameters'
        }, status=status.HTTP_400_BAD_REQUEST)


class PaymentProviderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        if request.query_params.get('query') == 'all':
            providers = PaymentProvider.objects.all()

            serializer = PaymentProviderListSerializer(providers, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        elif request.query_params.get('query') == 'active':
            providers = PaymentProvider.objects.filter(is_active=True)
            serializer = PaymentProviderListSerializer(providers, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        elif request.query_params.get('query') == 'deposit':
            fiat_providers = PaymentProvider.objects.filter(is_active=True, is_crypto=False)
            crypto_providers = PaymentProvider.objects.filter(is_active=True, is_crypto=True)
            fiat_serializer = PaymentProviderListSerializer(fiat_providers, many=True)
            for index, provider in enumerate(fiat_serializer.data):
                reversed = sorted(provider['methods'], key=lambda x: x['name'], reverse=True)
                fiat_serializer.data[index]['methods'] = reversed
            crypto_serializer = PaymentProviderListSerializer(crypto_providers, many=True)
            return Response(data={
                'fiat': fiat_serializer.data,
                'crypto': crypto_serializer.data
            }, status=status.HTTP_200_OK)

        elif request.query_params.get('query') == 'withdrawal':
            fiat_providers = PaymentProvider.objects.filter(is_crypto=False, withdrawal=True)
            crypto_providers = PaymentProvider.objects.filter(is_crypto=True, withdrawal=True)
            fiat_serializer = PaymentProviderListSerializer(fiat_providers, many=True)
            for index, provider in enumerate(fiat_serializer.data):
                reversed = sorted(provider['methods'], key=lambda x: x['name'], reverse=True)
                fiat_serializer.data[index]['methods'] = reversed
            crypto_serializer = PaymentProviderListSerializer(crypto_providers, many=True)
            return Response(data={
                'fiat': fiat_serializer.data,
                'crypto': crypto_serializer.data
            }, status=status.HTTP_200_OK)

        else:
            providers = PaymentProvider.objects.filter(is_active=True,
                                                       payment_methods__name=request.query_params.get('query'))
            if providers:
                serializer = PaymentProviderListSerializer(providers, many=True)
                return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class DepositView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        serializer = DepositSerializer(data=request.query_params)
        if serializer.is_valid():
            transaction_id = uuid4()
            user = UserAccount.objects.get_or_none(pk=request.user.id)
            provider = PaymentProvider.objects.get(name=serializer.data.get('provider'))
            print("provides ", str(provider))

            # PROCEED WITH THE TRANSACTION
            if user and provider:
                if currency := Currency.objects.get_or_none(iso=serializer.data.get('currency')):
                    wallet = Wallet.objects.get(user=user, currency=currency)

                    Transaction.objects.create(
                        transaction_id=transaction_id,
                        user=user,
                        initial_amount=serializer.data.get('amount'),
                        amount=serializer.data.get('amount'),
                        currency=currency,
                        transaction_type='deposit',
                        transaction_status='pending',
                        balance=wallet.balance,
                        payment_provider=provider,
                    )

                    # HANDLE WONDERLANDPAY PAYMENT SPECIFICATION
                    if provider.name == 'wonderlandpay':
                        url = get_wonderlandpay_redirect_url(user, provider, currency, str(transaction_id),
                                                             serializer.data.get('amount'))

                    # HANDLE INTERKASSA PAYMENT SPECIFICATION
                    if provider.name == 'interkassa':
                        url = get_interkassa_redirect_url(user, provider, currency, str(transaction_id),
                                                          serializer.data.get('amount'))
                    # HANDLE ENSOPAY PAYMENT SPECIFICATIONS
                    if provider.name == 'ensopay':
                        data = get_ensopay_redirect_url(user, provider, str(transaction_id),
                                                        serializer.data.get('amount'))
                        if data['status'] == 'error':
                            print('ensopay error is ' + data['errorMessage'])
                            return Response({'errorMessage': data['errorMessage']}, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            url = data['link']

                    # HANDLE ODEONPAY PAYMENT SPECIFICATIONS
                    if provider.name == 'odeonpay':
                        ip = take_user_ip(request)
                        data = get_odeonpay_redirect_url(user, provider, str(transaction_id),
                                                         serializer.data.get('amount'),
                                                         ip)
                        if data['status'] == 'error':
                            print('odeonpay error is ' + data['errorMessage'])
                            return Response({'errorMessage': data['errorMessage']}, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            print('data is    ' + str(data))
                            url = data['link']['action']

                    # HANDLE SYSPAY PAYMENT SPECIFICATIONS
                    if provider.name == 'syspay':
                        ip = take_user_ip(request)
                        url = get_syspay_redirect_url(user, provider, str(transaction_id),
                                                      serializer.data.get('currency'), serializer.data.get('amount'),
                                                      ip)

                    # HANDLE NEOBANQ PAYMENT SPECIFICATIONS
                    if provider.name == 'neobanq':
                        data = get_neobanq_redirect_url(user, provider, str(transaction_id),
                                                       serializer.data.get('currency'), serializer.data.get('amount'))


                        if data['status'] == 'error':
                            return Response({'errorMessage': data['errorMessage']}, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            url = data['url']
                            
                    # HANDLE PAYECARDS PAYMENT SPECIFICATIONS
                    if provider.name == 'payecards':
                        url = get_payecards_redirect_url(user, provider, str(transaction_id),
                                                         serializer.data.get('currency'), serializer.data.get('amount'))

                    # HANDLE FINTECHCASHIER PAYMENT SPECIFICATIONS
                    if provider.name == 'fintech_cashier':
                        url = get_fintech_cashier_redirect_url(user, provider, currency, str(transaction_id),
                                                               serializer.data.get('amount'))

                    if provider.name == 'certus':
                        url = get_certus_redirect_url(user, provider, str(transaction_id),
                                                      serializer.data.get('currency'), serializer.data.get('amount'))

                    return Response({'url': url}, status=status.HTTP_200_OK, )

        return Response(status=status.HTTP_400_BAD_REQUEST)


class WithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        serializer = WithdrawalSerializer(data=request.data)
        if serializer.is_valid():
            details = serializer.data
            details['channel'] = 'USD'

            transaction_id = uuid4()
            user = UserAccount.objects.get_or_none(pk=request.user.id)
            provider = PaymentProvider.objects.get(name=serializer.data.get('provider'))

            # CHECK IF USER PROFILE IS COMPLETE
            for each in ['first_name', 'last_name', 'email', 'phone_number',
                         'country', 'city', 'address', 'zip', 'is_pep', 'identification_number']:
                if getattr(user, each) is None:
                    return Response(
                        data={
                            'message': 'incomplete profile',
                            'suggestion': 'fill out your profile',
                            'field': each
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # IF USER AND PROVIDER EXIST
            if user and provider:
                if currency := Currency.objects.get_or_none(iso='USD'):
                    wallet = Wallet.objects.get(user=user, currency=currency)

                    # IF USER HAS INSUFFICIENT FUNDS
                    if serializer.data.get('amount') > wallet.balance:
                        return Response(
                            data={
                                'message': 'Insufficient funds',
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    Transaction.objects.create(
                        transaction_id=transaction_id,
                        user=user,
                        initial_amount=serializer.data.get('amount'),
                        amount=serializer.data.get('amount'),
                        currency=currency,
                        transaction_type='withdrawal',
                        transaction_status='pending',
                        balance=wallet.balance,
                        payment_provider=provider,
                        details=details
                    )

                    # DEDUCT THE AMOUNT FROM THE BALANCE
                    wallet.balance -= serializer.data.get('amount')
                    wallet.save()

                    # RETURN THE STATUS CODE
                    return Response(data={
                        "message": "withdrawal request was created successfully"
                    }, status=status.HTTP_200_OK)

        return Response(data={
            "message": "invalid data"
        }, status=status.HTTP_400_BAD_REQUEST)


class IBANWithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        print(request.query_params)
        serializer = IBANWithdrawalSerializer(data=request.query_params)
        if serializer.is_valid():
            transaction_id = uuid4()
            user = UserAccount.objects.get_or_none(pk=request.user.id)
            provider = PaymentProvider.objects.get(name=serializer.data.get('provider'))

            # CHECK IF USER PROFILE IS COMPLETE
            for each in ['first_name', 'last_name', 'email', 'phone_number',
                         'country', 'city', 'address', 'zip', 'is_pep', 'identification_number']:
                if getattr(user, each) is None:
                    return Response(
                        data={
                            'message': 'incomplete profile',
                            'suggestion': 'fill out your profile',
                            'field': each
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # IF USER AND PROVIDER EXIST
            if user and provider:
                if currency := Currency.objects.get_or_none(iso=serializer.data.get('currency')):
                    wallet = Wallet.objects.get(user=user, currency=currency)

                    # IF USER HAS INSUFFICIENT FUNDS
                    if serializer.data.get('amount') > wallet.balance:
                        return Response(
                            data={
                                'message': 'Insufficient funds',
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    description = f"SWIFT/BIC - {serializer.data.get('swift')}; BANK ADDRESS - {serializer.data.get('bank_address')}"

                    transaction = Transaction.objects.create(
                        transaction_id=transaction_id,
                        user=user,
                        initial_amount=serializer.data.get('amount'),
                        amount=serializer.data.get('amount'),
                        currency=currency,
                        transaction_type='withdrawal',
                        transaction_status='pending',
                        transaction_order_number=serializer.data.get('iban'),
                        balance=wallet.balance,
                        description=description,
                        payment_provider=provider,
                    )

                    # CUT THE AMOUNT FROM THE BALANCE
                    wallet.balance -= serializer.data.get('amount')
                    wallet.save()

                    # HERE WE SHOULD HANDLE THE CONDICTION OF THE TRANSACTION
                    # FIRST MIGHT BE A WONDERLANDPAY

                    # RETURN CREATED WITHDRAWAL
                    serializer = UserWithdrawalSerializer(transaction)

                    # RETURN THE STATUS CODE .
                    return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserWithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        transactions = Transaction.objects.filter(transaction_type='withdrawal',
                                                  transaction_status='pending',
                                                  user=request.user)
        serializer = UserWithdrawalSerializer(transactions, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        transaction_id = request.data.get('transaction_id')
        transaction = Transaction.objects.get_or_none(transaction_id=transaction_id)

        if transaction and request.data.get('action') == 'cancel':
            user = UserAccount.objects.get_or_none(pk=request.user.id)
            user_wallet = Wallet.objects.get_or_none(user=user, currency=transaction.currency)

            # UPDATE USER BALANCE
            user_wallet.balance += transaction.initial_amount
            user_wallet.save()

            # CHANGE THE STATUS OF THE TRANSACTION
            transaction.transaction_status = 'deleted'
            transaction.transaction_end_date = timezone.now()
            transaction.save()

            # GET LEFT WITHDRAWALS
            transactions = Transaction.objects.filter(transaction_type='withdrawal',
                                                      transaction_status='pending',
                                                      user=request.user)
            serializer = UserWithdrawalSerializer(transactions, many=True)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class DixonPayDepositView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        serializer = DixonPayDepositSerializer(data=request.data)

        if serializer.is_valid():
            transaction_id = uuid4()
            user = UserAccount.objects.get_or_none(pk=request.user.id)
            provider = PaymentProvider.objects.get(name='dixonpay')

            # PROCEED WITH THE TRANSACTION
            if user and provider:
                if currency := Currency.objects.get_or_none(iso=serializer.data.get('currency')):
                    wallet = Wallet.objects.get(user=user, currency=currency)

                    print(serializer.data)

                    Transaction.objects.create(
                        transaction_id=transaction_id,
                        user=user,
                        initial_amount=serializer.data.get('amount'),
                        amount=serializer.data.get('amount'),
                        currency=currency,
                        transaction_type='deposit',
                        transaction_status='pending',
                        balance=wallet.balance,
                        payment_provider=provider,
                    )

                    if provider.testing:
                        endpoint = provider.test_endpoint
                        sign_key = provider.test_sign_key
                    else:
                        endpoint = provider.prod_endpoint
                        sign_key = provider.prod_sign_key

                    notifyUrl = 'https://mima-poker.cc/api/payment/dixonpay/callback/'

                    # CREATE ENCRYPTION
                    sign_data = provider.merchant_number + provider.gateway_number + str(transaction_id) + currency.iso + \
                        serializer.data.get("amount") + serializer.data.get("card_no") + ('20' + serializer.data.get("card_expire_year")) + \
                        serializer.data.get("card_expire_month") + serializer.data.get("card_security_code") + sign_key

                    sign_data_binary = sign_data.encode('utf-8')
                    encryption = hashlib.sha256(sign_data_binary).hexdigest()

                    data = {
                        'merNo': provider.merchant_number,
                        'terminalNo': provider.gateway_number,
                        'orderNo': str(transaction_id),
                        'orderCurrency': currency.iso,
                        'orderAmount': serializer.data.get("amount"),
                        'notifyUrl': notifyUrl,
                        'cardNo': serializer.data.get("card_no"),
                        'cardExpireMonth': serializer.data.get("card_expire_month"),
                        'cardExpireYear': ('20' + serializer.data.get("card_expire_year")),
                        'cardSecurityCode': serializer.data.get("card_security_code"),
                        'firstName': user.first_name,
                        'lastName': user.last_name,
                        'email': user.email,
                        'ip': '65.21.156.123',
                        'phone': user.phone_number,
                        'country': user.country[:2].upper(),
                        'city': user.city,
                        'address': user.address,
                        'zip': user.zip,
                        'encryption': encryption,
                        'webSite': 'mima-poker.cc',
                        'uniqueId': transaction_id
                    }

                    s2s_send_transaction.delay(endpoint, data)

                    return Response(data=data, status=status.HTTP_200_OK)

                return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class DixonPayCallback(APIView):
    permission_classes = [DixonPayCallbackPermission]

    def post(self, request, **kwargs):
        print(request.data)
        try:
            transaction = Transaction.objects.get(
                transaction_id=request.data.get('orderNo')
            )

            if transaction.transaction_status != 'success':
                if request.data.get('orderStatus') == '1':
                    transaction_status = 'success'
                    # UPDATE LIVE DEPOSIT FOR THE USER
                    currency = Currency.objects.get(iso=request.data.get('orderCurrency'))
                    wallet = Wallet.objects.get(
                        user=transaction.user,
                        currency=currency
                    )
                    wallet.balance += transaction.amount
                    wallet.save()
                else:
                    transaction_status = 'deleted'

                transaction.transaction_status = transaction_status
                transaction.transaction_order_number = request.data.get('tradeNo')
                transaction.transaction_end_date = timezone.now()
                transaction.save()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'Unsuccessful'},
                            status=status.HTTP_400_BAD_REQUEST)


class InterkassaCallback(APIView):
    permission_classes = [InterkassaCallbackPermission]

    def post(self, request, **kwargs):
        print(request.data)
        try:
            transaction = Transaction.objects.get(
                transaction_id=request.data.get('ik_pm_no')
            )

            if transaction.transaction_status != 'success':
                if request.data.get('ik_inv_st') == 'success':
                    transaction_status = 'success'
                    # UPDATE LIVE DEPOSIT FOR THE USER
                    currency = Currency.objects.get(iso=request.data.get('ik_cur'))
                    wallet = Wallet.objects.get(
                        user=transaction.user,
                        currency=currency
                    )
                    wallet.balance += transaction.amount
                    wallet.save()
                else:
                    transaction_status = 'deleted'

                transaction.transaction_status = transaction_status
                transaction.transaction_order_number = request.data.get('tradeNo')
                transaction.transaction_end_date = timezone.now()
                transaction.save()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'Unsuccessful'},
                            status=status.HTTP_400_BAD_REQUEST)


class InterkassaWithdrawalCallback(APIView):
    premission_classeses = [InterkassaCallbackPermission]

    def post(self, request, **kwargs):
        print(request.data)
        try:
            transaction = Transaction.objects.get(
                transaction_id=request.data.get('paymentNo')
            )

            if transaction.transaction_status != 'success' and transaction.transaction_status != 'deleted':
                if request.data.get('state') == 'success':
                    transaction_status = 'success'
                else:
                    # UPDATE LIVE DEPOSIT FOR THE USER
                    wallet = Wallet.objects.get(
                        user=transaction.user,
                        currency__iso='USD'
                    )
                    transaction_status = 'deleted'

                    wallet.balance += transaction.amount
                    wallet.save()

                transaction.transaction_status = transaction_status
                transaction.transaction_order_number = request.data.get('id')
                transaction.transaction_end_date = timezone.now()
                transaction.details = request.data

                transaction.save()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'Unsuccessful'},
                            status=status.HTTP_400_BAD_REQUEST)


class WonderlandPayCallback(APIView):
    permission_classes = [WonderlandPayCallbackPermission]

    def post(self, request, **kwargs):
        print(request.data)
        try:
            transaction = Transaction.objects.get(
                transaction_id=request.data.get('orderNo')
            )

            if transaction.transaction_status != 'success':
                if request.data.get('orderStatus') == '1':
                    transaction_status = 'success'
                    # UPDATE LIVE DEPOSIT FOR THE USER
                    currency = Currency.objects.get(iso=request.data.get('orderCurrency'))
                    wallet = Wallet.objects.get(
                        user=transaction.user,
                        currency=currency
                    )
                    wallet.balance += transaction.amount
                    wallet.save()
                else:
                    transaction_status = 'deleted'

                transaction.transaction_status = transaction_status
                transaction.transaction_order_number = request.data.get('tradeNo')
                transaction.transaction_end_date = timezone.now()
                transaction.save()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'Unsuccessful'},
                            status=status.HTTP_400_BAD_REQUEST)


class AlphaPoCallback(APIView):
    permission_classes = [AlphaPoCallbackPermission]

    def post(self, request, **kwargs):
        data = request.data
        print(data)

        if data.get('type') == 'deposit_exchange':
            provider = PaymentProvider.objects.get(name='alphapo')
            user = UserAccount.objects.get(pk=data['crypto_address']['foreign_id'])

            transaction = Transaction.objects.get_or_none(
                transaction_order_number=f"alphapo_{data['id']}")

            # CHECK IF IT IS NOT A REPETATIVE TRANSACTION
            if not transaction:
                wallet = Wallet.objects.get(user=user, currency__iso='USD')
                description = json.dumps(data, separators=(',', ':'))

                if data['status'] == 'confirmed':
                    if currency := Currency.objects.get_or_none(iso=request.data['currency_sent']['currency']):
                        rate = float(data['currency_received']['amount']) / float(data['currency_sent']['amount'])

                        try:
                            transaction, created = Transaction.objects.get_or_create(
                                transaction_id=uuid4(),
                                user=user,
                                initial_amount=float(data['currency_sent']['amount']),
                                amount=float(data['currency_received']['amount']),
                                currency=currency,
                                rate=rate,
                                fee=float(data['fees'][0].get('amount')),
                                transaction_type='deposit_exchange',
                                transaction_status='success',
                                transaction_order_number=f"alphapo_{data['id']}",
                                balance=wallet.balance,
                                payment_provider=provider,
                                description=description,
                                transaction_end_date=timezone.now()
                            )

                            if created:
                                wallet.balance += transaction.amount
                                wallet.save()

                        except IntegrityError:
                            print('not creating a duplicate transaction')

                elif data['status'] == 'cancelled':
                    if currency := Currency.objects.get_or_none(iso=request.data['transactions'][1]['currency']):
                        transaction = Transaction.objects.create(
                            transaction_id=uuid4(),
                            user=user,
                            initial_amount=float(data['transactions'][1]['amount']),
                            amount=float(data['transactions'][1]['amount_to']),
                            currency=currency,
                            transaction_type='deposit_exchange',
                            transaction_status='deleted',
                            transaction_order_number=data['id'],
                            balance=wallet.balance,
                            payment_provider=provider,
                            description=description,
                            transaction_end_date=timezone.now()
                        )
                elif data['status'] == 'not_confirmed':
                    if currency := Currency.objects.get_or_none(iso=request.data['currency_sent']['currency']):
                        rate = float(data['currency_received']['amount']) / float(data['currency_sent']['amount'])

                        transaction = Transaction.objects.create(
                            transaction_id=uuid4(),
                            user=user,
                            initial_amount=float(data['currency_sent']['amount']),
                            amount=float(data['currency_received']['amount_minus_fee']),
                            currency=currency,
                            rate=rate,
                            transaction_type='deposit_exchange',
                            transaction_status='pending',
                            transaction_order_number=data['id'],
                            balance=wallet.balance,
                            payment_provider=provider,
                            description=description,
                            transaction_end_date=timezone.now()
                        )

            elif transaction and transaction.transaction_status == 'pending':
                if data['status'] == 'confirmed':
                    transaction.transaction_status = 'success'
                    transaction.fee = float(data['fees'][0].get('amount'))
                    transaction.save()

                    wallet = Wallet.objects.get(user=user, currency__iso='USD')
                    wallet.balance += transaction.amount
                    wallet.save()
                elif data['status'] == 'cancelled':
                    transaction.transaction_status = 'deleted'
                    transaction.save()

        elif data.get('type') == 'withdrawal_exchange':
            transaction = Transaction.objects.get_or_none(transaction_id=UUID(data.get('foreign_id')))

            if transaction and transaction.transaction_status == 'pending':
                transaction.transaction_status = 'success' if data.get('status') == 'confirmed' else 'deleted'
                transaction.description = json.dumps(data)
                transaction.save()

                if transaction.transaction_status == 'deleted':
                    wallet = Wallet.objects.get_or_none(user=transaction.user, currency__iso='USD')
                    wallet.balance += transaction.amount
                    wallet.save()

        return Response(status=status.HTTP_200_OK)


class EnsopayCallback(APIView):
    permission_classes = [EnsopayCallbackPermission]

    def post(self, request, **kwargs):
        print(request.data)
        try:
            transaction = Transaction.objects.get(
                transaction_id=request.data.get('order_id')
            )
            if transaction.transaction_status != 'success':
                if request.data.get('payment_status') == "3":
                    transaction_status = 'success'
                    request_currency = 'USD'
                    # UPDATE LIVE DEPOSIT FOR THE USER
                    currency = Currency.objects.get(iso=request_currency.upper())
                    wallet = Wallet.objects.get(
                        user=transaction.user,
                        currency=currency
                    )
                    wallet.balance += transaction.amount
                    wallet.save()
                else:
                    transaction_status = 'deleted'

                transaction.transaction_status = transaction_status
                transaction.transaction_order_number = 'ensopay-' + str(request.data.get('payment_id'))
                transaction.transaction_end_date = timezone.now()
                transaction.save()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'Unsuccessful'},
                            status=status.HTTP_400_BAD_REQUEST)


class OdeonpayCallback(APIView):
    permission_classes = [OdeonpayCallbackPermission]

    def post(self, request, **kwargs):
        print(request.data)
        try:
            transaction = Transaction.objects.get(
                transaction_id=request.data.get('invoiceId')
            )
            if transaction.transaction_status != 'success':
                if request.data.get('statusCode') == 4:
                    transaction_status = 'success'
                    #request_currency = request.data.get('currency')
                    # UPDATE LIVE DEPOSIT FOR THE USER
                    currency = Currency.objects.get('USD')
                    wallet = Wallet.objects.get(
                        user=transaction.user,
                        currency=currency
                    )
                    wallet.balance += transaction.amount
                    wallet.save()
                    transaction.transaction_token = request.data.get('token')
                    print('token iss   ' + request.data.get('token'))
                elif request.data.get('statusCode') == 7:
                    transaction_status = 'success'
                elif request.data.get('statusCode') == 99:
                    transaction_status = 'deleted'
                elif request.data.get('statusCode') == 10:
                    return Response({"code": 0}, status=status.HTTP_200_OK)

                transaction.transaction_status = transaction_status
                transaction.transaction_order_number = request.data.get('transactionId')
                transaction.transaction_end_date = timezone.now()
                transaction.save()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'Unsuccessful'+str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


class OdeonpayWithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        serializer = OdeonpayWithdrawalSerializer(data=request.data)
        if serializer.is_valid():
            transaction_id = uuid4()
            user = UserAccount.objects.get_or_none(pk=request.user.id)
            provider = PaymentProvider.objects.get(name=serializer.data.get('provider'))

            # CHECK IF USER PROFILE IS COMPLETE
            for each in ['first_name', 'last_name', 'email', 'phone_number',
                         'country', 'city', 'address', 'zip', 'is_pep', 'identification_number']:
                if getattr(user, each) is None:
                    return Response(
                        data={
                            'message': 'incomplete profile',
                            'suggestion': 'fill out your profile',
                            'field': each
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # IF USER AND PROVIDER EXIST
            if user and provider:
                if currency := Currency.objects.get_or_none(iso=serializer.data.get('currency')):
                    wallet = Wallet.objects.get(user=user, currency=currency)

                    # IF USER HAS INSUFFICIENT FUNDS
                    if serializer.data.get('amount') > wallet.balance:
                        return Response(
                            data={
                                'message': 'Insufficient funds',
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # CUT THE AMOUNT FROM THE BALANCE
                    wallet.balance -= serializer.data.get('amount')
                    wallet.save()

                    # HERE WE SHOULD HANDLE THE CONDICTION OF THE TRANSACTION
                    # FIRST MIGHT BE A WONDERLANDPAY
                    RUB_amount = get_currency(serializer.data.get('amount'), 'RUB')
                    if provider.name == 'odeonpay':
                        data = {
                            'pan': serializer.data.get('card_number'),
                            'name': serializer.data.get('card_name'),
                            'amount': RUB_amount,
                            'currency': 'RUB',
                            'invoiceId': str(transaction_id),
                            'phone': user.phone_number
                        }
                    Transaction.objects.create(
                        transaction_id=transaction_id,
                        user=user,
                        initial_amount=serializer.data.get('amount'),
                        amount=serializer.data.get('amount'),
                        currency=currency,
                        transaction_type='withdrawal',
                        transaction_status='pending',
                        balance=wallet.balance,
                        payment_provider=provider,
                        details=data
                    )

                    # RETURN THE STATUS CODE
                    return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class TransactionHistory(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        print(request.query_params)
        serializer = TransactionHistoryRequestSerializer(data=request.query_params)

        if serializer.is_valid():
            user = UserAccount.objects.get_or_none(pk=request.user.id)
            page = serializer.data.get('page')
            limit = serializer.data.get('limit')
            start_date = serializer.data.get('start_date')
            end_date = serializer.data.get('stop_date')
            type = serializer.data.get('type')
            if type == 'all':
                type = ''

            limit_start = (page - 1) * limit
            limit_end = limit_start + limit
            transactions = Transaction.objects.select_related('currency', 'payment_provider',
                                                              'game').filter(
                user=user, transaction_start_date__date__gte=start_date,
                transaction_start_date__date__lte=end_date,
                transaction_type__contains=type
            ).order_by('-transaction_start_date')
            transaction_count = transactions.count()
            page_count = (transaction_count // limit) + (1 if transaction_count % limit > 0 else 0)
            transactions = transactions[limit_start:limit_end]
            transaction_serializer = TransactionHistorySerializer(transactions, many=True)

            response_data = dict()
            response_data['transactions'] = transaction_serializer.data
            response_data['transactions_total'] = transaction_count
            response_data['page_count'] = page_count
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(status=status.HTTP_400_BAD_REQUEST)


class SyspayCallback(APIView):
    permission_classes = [SyspayCallbackPermission]

    @csrf_exempt
    def post(self, request, **kwargs):

        print("syspay receive data ", request.data)
        try:
            pay_url = request.data.get('pay_url')
            print('pay_url')
            return redirect(pay_url)
        except Exception as e:
            print('without pay _ url')
            try:
                transaction = Transaction.objects.get(
                    transaction_id=request.data.get('id_order')
                )
                if transaction.transaction_status != 'success':
                    if request.data.get('status_nm') == '9':
                        transaction_status = 'success'
                        request_currency = request.data.get('curr')
                        # UPDATE LIVE DEPOSIT FOR THE USER
                        currency = Currency.objects.get(iso=request_currency.upper())
                        wallet = Wallet.objects.get(
                            user=transaction.user,
                            currency=currency
                        )
                        wallet.balance += transaction.amount
                        wallet.save()

                    elif request.data.get('status_nm') == '1':
                        transaction_status = 'success'
                        request_currency = request.data.get('curr')
                        # UPDATE LIVE DEPOSIT FOR THE USER
                        currency = Currency.objects.get(iso=request_currency.upper())
                        wallet = Wallet.objects.get(
                            user=transaction.user,
                            currency=currency
                        )
                        wallet.balance += transaction.amount
                        wallet.save()
                    elif request.data.get('status_nm') == '2':
                        transaction_status = 'deleted'
                    elif request.data.get('status_nm') == '0':
                        transaction_status = 'pending'
                    else:
                        transaction_status = 'deleted'

                    transaction.transaction_status = transaction_status
                    transaction.transaction_order_number = 'syspay-' + str(request.data.get('transaction_id'))
                    transaction.transaction_end_date = timezone.now()
                    transaction.save()

                return Response(status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({'message': 'Unsuccessful'},
                                status=status.HTTP_400_BAD_REQUEST)


class NeobanqCallback(APIView):

    def post(self, request, **kwargs):

        try:
            transaction = Transaction.objects.get(
                transaction_id=request.data.get('sulte_apt_no')
            )
            if transaction.transaction_status != 'success':
                if str(transaction.payment_provider) == 'neobanq':
                    provider = PaymentProvider.objects.get(
                        name='neobanq'
                    )
                    endpoint = provider.website
                    if provider.testing:
                        sign_key = provider.test_sign_key
                    else:
                        sign_key = provider.prod_sign_key

                    data = {
                        'api_key': sign_key,
                        'sulte_apt_no': request.data.get('sulte_apt_no'),
                        'order_id': request.data.get('order_id')
                    }

                    response = requests.post(endpoint + 'get/transaction', json=data)
                    print(response.text)

                    if response.status_code == 200:
                        response = response.json()
                        print(response['transaction']['transaction_status'])
                        if str(response['transaction']['transaction_status']) == 'success':
                            transaction.description = str(response)
                            transaction_status = 'success'
                            request_currency = response['transaction']['currency']
                            # UPDATE LIVE DEPOSIT FOR THE USER
                            currency = Currency.objects.get(iso=request_currency.upper())
                            wallet = Wallet.objects.get(
                                user=transaction.user,
                                currency=currency
                            )
                            wallet.balance += transaction.amount
                            wallet.save()
                        elif str(response['transaction']['transaction_status']) == 'fail':
                            transaction_status = 'deleted'
                            transaction.description = str(response)
                        elif str(response['transaction']['transaction_status']) == 'pending':
                            transaction_status = 'pending'
                            transaction.description = str(response)

                transaction.transaction_status = transaction_status
                transaction.transaction_order_number = 'neobanq-'+str(request.data.get('order_id'))
                transaction.transaction_end_date = timezone.now()
                transaction.save()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'Unsuccessful'},
                            status=status.HTTP_400_BAD_REQUEST)


class PayecardsCallback(APIView):
    # permission_classes = [SyspayCallbackPermission]

    def post(self, request, **kwargs):
        print(request.data)
        try:
            transaction = Transaction.objects.get(
                transaction_id=request.data.get('Custom1')
            )
            if transaction.transaction_status != 'success':
                if request.data.get('status_nm') == '9':
                    transaction_status = 'success'
                    request_currency = request.data.get('curr')
                    # UPDATE LIVE DEPOSIT FOR THE USER
                    currency = Currency.objects.get(iso=request_currency.upper())
                    wallet = Wallet.objects.get(
                        user=transaction.user,
                        currency=currency
                    )
                    wallet.balance += transaction.amount
                    wallet.save()
                elif request.data.get('status_nm') == '1':
                    transaction_status = 'success'
                    request_currency = request.data.get('curr')
                    # UPDATE LIVE DEPOSIT FOR THE USER
                    currency = Currency.objects.get(iso=request_currency.upper())
                    wallet = Wallet.objects.get(
                        user=transaction.user,
                        currency=currency
                    )
                    wallet.balance += transaction.amount
                    wallet.save()
                elif request.data.get('status_nm') == '2':
                    transaction_status = 'deleted'
                elif request.data.get('status_nm') == '0':
                    transaction_status = 'pending'
                else:
                    transaction_status = 'deleted'

                transaction.transaction_status = transaction_status
                transaction.transaction_order_number = request.data.get('transaction_id')
                transaction.transaction_end_date = timezone.now()
                transaction.save()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'Unsuccessful'},
                            status=status.HTTP_400_BAD_REQUEST)


class SyspayPaymentSuccess(APIView):
    @csrf_exempt
    def post(self, request, **kwargs):
        print(request.data)
        provider = PaymentProvider.objects.get(
            name='syspay'
        )
        if provider.testing:
            endpoint = provider.test_endpoint
        else:
            endpoint = provider.prod_endpoint

        return redirect(str(endpoint) + '/payment-success')


class SyspayPaymentFail(APIView):
    @csrf_exempt
    def post(self, request, **kwargs):
        print(request.data)
        provider = PaymentProvider.objects.get(
            name='syspay'
        )
        if provider.testing:
            endpoint = provider.test_endpoint
        else:
            endpoint = provider.prod_endpoint

        return redirect(str(endpoint) + '/payment-failed')


class FintechCashierDepositCallback(APIView):
    permission_classes = [FintechCashierCallbackPermission]

    def post(self, request):
        data = request.data
        print(data)

        transaction = Transaction.objects.get(
            transaction_id=data.get('trans_order')
        )

        if transaction.transaction_status != 'success':
            if data.get('reply_code') == '000':
                transaction_status = 'success'

                # UPDATE LIVE DEPOSIT FOR THE USER
                currency = Currency.objects.get(iso=data.get('trans_currency'))
                wallet = Wallet.objects.get(
                    user=transaction.user,
                    currency=currency
                )
                wallet.balance += transaction.amount
                wallet.save()
            else:
                transaction_status = 'deleted'

            transaction.transaction_status = transaction_status
            transaction.transaction_order_number = f'fintech_cashier_{data.get("trans_id")}'
            transaction.transaction_end_date = timezone.now()
            transaction.description = json.dumps(data, separators=(',', ':'))
            transaction.save()

        return Response(status=status.HTTP_200_OK)

    def get(self, request):
        print(request.query_params)

        return Response(status=status.HTTP_200_OK)


class CertusCallback(APIView):

    permission_classes = [CertusCallbackPermission]

    def post(self, request, **kwargs):
        print(request.data)
        try:
            transaction = Transaction.objects.get(
                transaction_id=request.data.get('orderId')
            )
            if transaction.transaction_status != 'success':
                if request.data['result']['resultCode'] == "1":
                    transaction_status = 'success'
                    request_currency = 'USD'
                    # UPDATE LIVE DEPOSIT FOR THE USER
                    currency = Currency.objects.get(iso=request_currency.upper())
                    wallet = Wallet.objects.get(
                        user=transaction.user,
                        currency=currency
                    )
                    wallet.balance += transaction.amount
                    wallet.save()
                else:
                    transaction_status = 'deleted'

                transaction.transaction_status = transaction_status
                transaction.transaction_order_number = 'certus-' + str(request.data.get('txId'))
                transaction.transaction_end_date = timezone.now()
                transaction.save()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'Unsuccessful'},
                            status=status.HTTP_400_BAD_REQUEST)
