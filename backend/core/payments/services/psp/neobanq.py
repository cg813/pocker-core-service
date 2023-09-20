import requests

from accounts.models import UserAccount, Currency
from payments.models import PaymentMethod


def get_neobanq_redirect_url(user: UserAccount, provider: PaymentMethod, transaction_id: str, currency: Currency,
                             amount: float) -> str:
    if provider.testing:
        endpoint = provider.test_endpoint
        sign_key = provider.test_sign_key
    else:
        endpoint = provider.prod_endpoint
        sign_key = provider.prod_sign_key

    url = str(provider.website) + 'hosted-pay/payment-request?' + 'api_key=' + str(sign_key) + '&first_name=' + str(
        user.username) + '&last_name=' + str(user.last_name) + '&address=' + '112 Bonadie Street' + \
        '&country=VC' + '&state=Vincent' + '&city=Kingstown' + '&zip=P.O Box 613' + '&email=' + user.email + '&phone_no=' + str(
        user.phone_number) + '&amount=' + str(amount) + '&currency=' + str(currency) + '&response_url=' +str(
        endpoint) + '/statuses' + '&sulte_apt_no=' + str(transaction_id)+'&webhook_url=' + str(endpoint) \
        + '/api/payment/neobanq/callback/'

    response = requests.post(url)
    print(response.text)

    if response.status_code == 200:
        response = response.json()
        if str(response['status']) == '3d_redirect':
            data = {'status': 'success', 'url': response['redirect_3ds_url']}
        else:
            data = {'status': 'error', 'errorMessage': response['message']}

    return data
