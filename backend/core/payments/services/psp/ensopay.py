import requests

from accounts.models import UserAccount, Rate, Currency
from payments.models import PaymentMethod
from payments.services.utils import get_currency

from datetime import datetime


def get_ensopay_redirect_url(user: UserAccount, provider: PaymentMethod, transaction_id: str, amount: float) -> str:
    if provider.testing:
        endpoint = provider.test_endpoint + '/invoice'
    else:
        endpoint = provider.prod_endpoint + '/invoice'

    generate_token = provider.gateway_number
    Date = datetime.date(datetime.now())
    rateString = Rate.objects.filter(currency_from=Currency.objects.get_or_none(iso='USD'), currency_to_string = 'EUR', created_at__startswith=Date).values('rate')
    print("rate is ", str(rateString))

    if rateString.exists():
        amount_EUR = amount * rateString[0].get('rate')
    else:
        amount_EUR = get_currency(amount, 'EUR')

    if amount_EUR != -1:
        data = {
            'amount': amount_EUR,
            'project': provider.merchant_number,
            'orderId': str(transaction_id),
            'description': f'{user.username} - deposit',
            'phone': user.phone_number,
            'Email': user.email
        }
        headers = {'Authorization': 'Bearer ' + generate_token}

        response = requests.post(endpoint, headers=headers, json=data)
        print(response.text)

        if response.status_code == 200:
            response = response.json()
            if str(response['status']) == 'ok':
                data = {'status': 'success', 'link': response['link']}
        else:
            print("bad request ")
            response = response.json()
            data = {'status': 'error', 'errorMessage': response['errorMessage']}
    else:
        data = {'status': 'error', 'errorMessage': 'CONVERTING ERROR'}

    return data
