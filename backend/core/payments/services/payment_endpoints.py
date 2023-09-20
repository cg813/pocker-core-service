import json
import hmac
import hashlib
from typing import Tuple
from rest_framework.serializers import Serializer

from accounts.models import Transaction, UserAccount
from payments.models import PaymentProvider


import requests
from requests.auth import HTTPBasicAuth


def get_min_deposit(user: UserAccount, currency_from, currency_to) -> UserAccount:
    '''
    IT GENERATES DEPOSIT EXCHANGE ADDRESS FOR USER TO PROCEED WITH THE PAYMENT
    :param user is an instance of UserAccount class
    :param currency_from is the currency that will be accepted as for initial payment
    :param currency_to is the currency to which the initial currency will be exchanged
    '''
    provider = PaymentProvider.objects.get_or_none(name='alphapo')

    merchant_number = provider.merchant_number

    if provider.testing:
        merchant_number = provider.merchant_number
        endpoint = f'{provider.test_endpoint}/currencies/pairs'
        secret = provider.test_sign_key.encode('utf-8')
    else:
        merchant_number = provider.gateway_number
        endpoint = f'{provider.prod_endpoint}/currencies/pairs'
        secret = provider.prod_sign_key.encode('utf_8')

    request_body = json.dumps({
        "currency_from": currency_from,
        "foreign_id": str(user.id),
        "convert_to": currency_to
    }, separators=(',', ':'))

    encoded_body = request_body.encode('utf-8')

    signature = hmac.new(
        secret,
        msg=encoded_body,
        digestmod=hashlib.sha512
    ).hexdigest()

    headers = {
        'X-Processing-Key': merchant_number,
        'X-Processing-Signature': signature,
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(endpoint, request_body, headers=headers)
        if currency_to == 'USD':
            specifications = response.json()['data'][-1]
            min_deposit = specifications['currency_from']['min_amount_deposit_with_exchange']
            rate = specifications['rate_to']
        elif currency_from == 'USD':
            if currency_to == 'BTC':
                specifications = response.json()['data'][0]
            elif currency_to == 'ETH':
                specifications = response.json()['data'][1]
            min_deposit = specifications['currency_from']['min_amount']
            rate = specifications['rate_to']
    except Exception as e:
        print(e)
        min_deposit = None
        rate = None

    return min_deposit, rate


def make_alphapo_withdrawal_exchange(transaction: Transaction):
    """ This function makes request to the alphapo to make withdrawal
    :param provider is an instance of a PaymentProvider class
    :param transaction_id is an internal id assigned to the transaction
    :param serialized_data is serialized data of the request
    """

    provider = PaymentProvider.objects.get_or_none(name='alphapo')

    merchant_number = provider.merchant_number

    if provider.testing:
        merchant_number = provider.merchant_number
        endpoint = f'{provider.test_endpoint}/withdrawal/crypto'
        secret = provider.test_sign_key.encode('utf-8')
    else:
        merchant_number = provider.gateway_number
        endpoint = f'{provider.prod_endpoint}/withdrawal/crypto'
        secret = provider.prod_sign_key.encode('utf_8')

    request_body = json.dumps({
        "foreign_id": str(transaction.transaction_id),
        "amount": str(transaction.details.get('amount')),
        "currency": transaction.details.get('currency_from'),
        "convert_to": transaction.details.get('currency_to'),
        "address": transaction.details.get('address')
    }, separators=(',', ':'))

    encoded_body = request_body.encode('utf_8')

    print(encoded_body)

    signature = hmac.new(
        secret,
        msg=encoded_body,
        digestmod=hashlib.sha512
    ).hexdigest()

    print(signature)

    headers = {
        'X-Processing-Key': merchant_number,
        'X-Processing-Signature': signature,
        'Content-Type': 'application/json'
    }

    response = requests.post(endpoint, request_body, headers=headers)
    status_code = response.status_code
    data = response.json()

    if status_code == 201:
        transaction_status = 'waiting_for_provider_confirmation'
        transaction_order_number = f"alphapo_{data['data']['id']}"
        rate = float(data['data']['sender_amount']) / float(data['data']['receiver_amount'])
    else:
        transaction_status = 'deleted'
        transaction_order_number = None
        rate = None

    transaction.description = json.dumps(data, ensure_ascii=False)
    transaction.amount = data['data']['receiver_amount'] if data.get('data') else 0
    transaction.rate = rate
    transaction.transaction_order_number = transaction_order_number
    transaction.transaction_status = transaction_status
    transaction.save()

    print(data)


def make_interkassa_withdrawal(transaction: Transaction):
    """ THIS FUNCTION WILL MAKE AN AUTOMATIC WITHDRAWAL REQUEST TO INTERKASS
    :param transaction is an instance of Transaction class """

    usd_channel = '200943226497'
    rub_channel = '407014523187'
    user = '60743bac73bb747c4d318cb3'
    password = '4qqYQZEyg1avVpTRpH3w75jc360T7ztc'
    base_url = 'https://api.interkassa.com/v1'

    session = requests.Session()
    session.auth = (user, password)

    auth = session.post(f'{base_url}/currency')
    response = session.get(f'{base_url}/currency')

    usd_to_uah_rate = response.json()['data']['USD']['UAH']['out']
    converted_amount = transaction.amount * usd_to_uah_rate

    if transaction.details.get('channel') == 'USD':
        purse_id = usd_channel
    elif transaction.details.get('channel') == 'RUB':
        purse_id = rub_channel

    data = {
        'amount': converted_amount,
        'purseId': purse_id,
        'method': 'card',
        'action': 'process',
        'paymentNo': str(transaction.transaction_id),
        'currency': 'UAH',
        'useShortAlias': True,
        'details[card]': transaction.details.get('card_number'),
        'details[card_month]': transaction.details.get('card_month'),
        'details[card_year]': transaction.details.get('card_year'),
        'details[card_holder]': transaction.details.get('card_holder'),
        'details[card_owner_birth]': transaction.user.birth_date,
        'details[phone]': transaction.user.phone_number,
        'details[city]': transaction.user.city
    }

    response = session.post(f'{base_url}/withdraw', data=data).json()

    if response.get('status') == 'ok':
        transaction.transaction_status = 'waiting_for_provider_confirmation'
    else:
        transaction.transaction_status = 'deleted'

    transaction.description = json.dumps(response, ensure_ascii=False)
    transaction.rate = usd_to_uah_rate
    transaction.save()

    print(data)
    print(response)


def get_currency(amount, currency):
    url = 'https://api.exchangerate.host/convert?from=USD&to='+currency
    response = requests.get(url)
    data = response.json()
    print(data)
    if response.status_code == 200:
        response = response.json()
        if response['success'] == True:
            rate = response['info']['rate']
            return str(rate), str(rate * amount)
        else:
            return -1, -1
    else:
        return -1, -1


def make_odeonpay_withdrawal(transaction: Transaction):
    """ THIS FUNCTION WILL MAKE AN AUTOMATIC WITHDRAWAL REQUEST TO odeonpay
    :param transaction is an instance of Transaction class """

    rate, get_RUB_amount = get_currency(transaction.amount, 'RUB')
    if rate == -1:
        return -1

    data = {
        'pan': transaction.details.get('card_number'),
        'name': transaction.details.get('card_name'),
        'amount': get_RUB_amount,
        "currency": "RUB",
        "invoiceId": str(transaction.transaction_id),
        "phone": transaction.user.phone_number,
    }
    payment_provider = PaymentProvider.objects.get_or_none(name=transaction.payment_provider)

    if payment_provider.testing:
        merchant_number = payment_provider.test_merchant_number
        endpoint = payment_provider.test_endpoint+'payments/payout/card'
        sign_key = payment_provider.test_sign_key
    else:
        merchant_number = payment_provider.merchant_number
        endpoint = payment_provider.prod_endpoint+'payments/payout/card'
        sign_key = payment_provider.prod_sign_key

    response = requests.post(endpoint, auth=HTTPBasicAuth(merchant_number, sign_key), json=data)
    print(type(response))

    if response.status_code == 200:
        transaction.transaction_status = 'waiting_for_provider_confirmation'
    else:
        transaction.transaction_status = 'deleted'

    transaction.description = json.dumps(response.json(), ensure_ascii=False)
    transaction.rate = rate
    transaction.save()

    print(data)
    print(response)
