from accounts.models import UserAccount, Currency
from payments.models import PaymentMethod


def get_payecards_redirect_url(user: UserAccount, provider: PaymentMethod, transaction_id: str, currency: Currency,
                               amount: float) -> str:
    if provider.testing:
        sign_key = provider.test_sign_key
    else:
        sign_key = provider.prod_sign_key

    url = str(provider.website) + '?Key=' + str(sign_key) + '&Amount=' + str(
        amount) + '&CurrencyCode=840' + '&FirstName=' + str(user.username) + \
        '&LastName=' + str(user.last_name) + '&Email=' + str(user.email) + '&Custom1=' + str(transaction_id)
    return url
