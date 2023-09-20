import os
import hashlib
import base64
import urllib

from accounts.models import UserAccount, Currency
from payments.models import PaymentProvider


def get_fintech_cashier_redirect_url(user: UserAccount, provider: PaymentProvider,
                                     currency: Currency, transaction_id: str, amount: float) -> str:
    if provider.testing:
        endpoint = provider.test_endpoint
        sign_key = provider.test_sign_key
    else:
        endpoint = provider.prod_endpoint
        sign_key = provider.prod_sign_key

    base_url = os.environ.get('CLIENT_GAME_URL')

    params = {
        'merchantID': provider.merchant_number,
        'notification_url': f'{base_url}/api/payment/fintech_cashier/callback/',
        'url_redirect': f'{base_url}/statuses',
        'trans_comment': '',
        'trans_refNum': transaction_id,
        'trans_installments': '1',
        'trans_type': '0',
        'trans_amount': int(amount),
        'trans_currency': currency.iso,
        'disp_paymentType': 'CC',
        'disp_payFor': 'Purchase',
        'disp_recurring': '0',
        'disp_lng': 'en-gb',
        'disp_mobile': 'auto',
        'billingState=': ''
    }

    sign_data = ''

    for value in params.items():
        sign_data += str(value[1])
    sign_data += sign_key

    sign_data_binary = sign_data.encode('utf-8')
    sign_info = base64.b64encode(hashlib.sha256(sign_data_binary).digest()).decode('utf-8')
    print(sign_info)

    params['signature'] = sign_info

    params = urllib.parse.urlencode(params)

    url = f"{endpoint}?{params}"

    # REPLACE EMPTY SPACES WITH %20
    url = url.replace(' ', '%20')
    print(url)

    return url
