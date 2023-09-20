import requests

from requests.auth import HTTPBasicAuth

from accounts.models import UserAccount, Currency, Rate
from payments.models import PaymentMethod
from payments.services.utils import get_currency

from datetime import datetime

def get_odeonpay_redirect_url(user: UserAccount, provider: PaymentMethod, transaction_id: str,
                              amount: float, ip: str) -> str:
    if provider.testing:
        merchant_number = provider.test_merchant_number
        endpoint = provider.test_endpoint + 'payments/link'
        sign_key = provider.test_sign_key
    else:
        merchant_number = provider.merchant_number
        endpoint = provider.prod_endpoint + 'payments/link'
        sign_key = provider.prod_sign_key

    Date = datetime.date(datetime.now())
    rateString = Rate.objects.filter(currency_from=Currency.objects.get_or_none(iso='USD'), currency_to_string='RUB',
                                     created_at__startswith=Date).values('rate')

    if rateString.exists():
        amount_RUB = amount * rateString[0].get('rate')
        print('amount_RUB  ', str(amount_RUB))
    else:
        amount_RUB = get_currency(amount, 'RUB')

    if amount_RUB != -1:
        data = {
            'amount': amount_RUB,
            'currency': 'RUB',
            'invoiceId': str(transaction_id),
            'description': f'{user.username} - deposit',
            'accountId': user.email,
            'successUrl': str(provider.website) + "payment-success/deposit",
            'failureUrl': str(provider.website) + "payment-failed/deposit",
            'pendingUrl': str(provider.website) + "payment-loading/deposit",
            'cancelUrl':  str(provider.website) + "payment-failed/deposit",
            'locale': 'en_US',
            'ip': ip,
            "data": {
                "personId": user.id,
                "phone": user.phone_number,
                "address": " ",
                "city": " ",
                "firstName": user.username,
                "lastName": user.last_name,
                "countryCode": "BR",
                "paymentTypeId": 1000
            }

        }

        response = requests.post(endpoint, auth=HTTPBasicAuth(merchant_number, sign_key), json=data)
        print(response.text)

        if response.status_code == 200:
            response = response.json()
            if str(response['success']):
                data = {'status': 'success', 'link': response['link']}
        else:
            print("bad request ")
            response = response.json()
            data = {'status': 'error', 'errorMessage': response['message']}
    else:
        data = {'status': 'error', 'errorMessage': 'CONVERTING ERROR'}

    return data
