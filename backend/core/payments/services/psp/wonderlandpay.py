import os
import hashlib

from accounts.models import UserAccount, Currency
from payments.models import PaymentProvider


def get_wonderlandpay_redirect_url(user: UserAccount, provider: PaymentProvider,
                                   currency: Currency, transaction_id: str, amount: float) -> str:
    if provider.testing:
        endpoint = provider.test_endpoint
        sign_key = provider.test_sign_key
    else:
        endpoint = provider.prod_endpoint
        sign_key = provider.prod_sign_key

    base_url = os.environ.get('CLIENT_GAME_URL')

    return_url = f'{base_url}/wonderlandpay'
    notify_url = f'{base_url}/api/payment/wonderlandpay/callback/'

    sign_data = (provider.merchant_number + provider.gateway_number + str(transaction_id) +
                 currency.iso + str(amount) + return_url + sign_key)

    sign_data_binary = sign_data.encode('utf-8')
    sign_info = hashlib.sha256(sign_data_binary).hexdigest()

    url = f"{endpoint}?merNo={provider.merchant_number}&" \
          f"gatewayNo={provider.gateway_number}&" \
          f"orderNo={transaction_id}&" \
          f"orderCurrency={currency.iso}&" \
          f"orderAmount={amount}&" \
          f"returnUrl={return_url}&" \
          f"notifyUrl={notify_url}&" \
          f"signInfo={sign_info}&" \
          f"firstName={user.first_name}&" \
          f"lastName={user.last_name}&" \
          f"email={user.email}&" \
          f"phone={user.phone_number}&" \
          f"country={user.country}&" \
          f"city={user.city}&" \
          f"address={user.address}&" \
          f"zip={user.zip}" \

    # REPLACE EMPTY SPACES WITH %20
    url = url.replace(' ', '%20')
    print(url)

    return url
