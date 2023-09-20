import json
import hmac
import hashlib
import requests
from accounts.models import UserAccount
from payments.models import PaymentProvider


def generate_alphapo_exchange_address(user: UserAccount, currency_from, currency_to) -> UserAccount:
    '''
    IT GENERATES DEPOSIT EXCHANGE ADDRESS FOR USER TO PROCEED WITH THE PAYMENT
    :param user is an instance of UserAccount class
    :param currency_from is the currency that will be accepted as for initial payment
    :param currency_to is the currency to which the initial currency will be exchanged
    '''
    provider = PaymentProvider.objects.get_or_none(name='alphapo')

    if provider.testing:
        merchant_number = provider.merchant_number
        endpoint = f'{provider.test_endpoint}/addresses/take'
        secret = provider.test_sign_key.encode('utf-8')
    else:
        merchant_number = provider.gateway_number
        endpoint = f'{provider.prod_endpoint}/addresses/take'
        secret = provider.prod_sign_key.encode('utf_8')

    request_body = json.dumps({
        "currency": currency_from,
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
        address = response.json()['data']['address']
    except Exception as e:
        print(e)
        address = None

    return address
