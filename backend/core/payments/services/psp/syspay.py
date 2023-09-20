from accounts.models import UserAccount, Currency
from payments.models import PaymentMethod


def get_syspay_redirect_url(user: UserAccount, provider: PaymentMethod, transaction_id: str, currency: Currency,
                            amount: float, ip: str) -> str:
    if provider.testing:
        merchant_number = provider.test_merchant_number
        endpoint = provider.test_endpoint
        sign_key = provider.gateway_number
    else:
        merchant_number = provider.merchant_number
        endpoint = provider.prod_endpoint
        sign_key = provider.gateway_number

    url = (str(provider.website) + '?' + 'website_id=' + str(merchant_number) + '&client_ip=' + ip
           + '&price=' + str(amount) + '&curr=' + str(currency) + '&api_token=' + str(sign_key)
           + '&product_name = syspay_payment' + 'Product&action=product' + '&notify_url='
           + str(endpoint) + '/api/payment/syspay/callback/'
           + '&success_url=' + str(endpoint) + '/api/payment/syspay/payment-success/'
           + '&error_url=' + str(endpoint) + '/api/payment/syspay/payment-failed/'
           + '&id_order=' + str(transaction_id)) + '&pay_mode=3d'

    print(url)
    return url
