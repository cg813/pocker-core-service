import requests

from accounts.models import UserAccount, Currency
from payments.models import PaymentMethod


def get_interkassa_redirect_url(user: UserAccount, provider: PaymentMethod,
                                currency: Currency, transaction_id: str, amount: float) -> str:
    if provider.testing:
        endpoint = provider.test_endpoint
    else:
        endpoint = provider.prod_endpoint

    data = {
        'ik_co_id': provider.merchant_number,
        'ik_pm_no': transaction_id,
        'ik_am': str(amount),
        'ik_cur': currency.iso,
        'ik_desc': f'{user.username} - deposit',
        # 'ik_act': 'payway',
        'ik_pw_via': 'card_cpaytrz_triplecHR_eur',
        'ik_int': 'json',
        'ik_act': 'process',
        # 'ik_pw_via': 'test_interkassa_test_xts'

    }

    response = requests.get(endpoint, data).json()

    message = response['resultData']['paymentForm']

    print(message)
    return message
