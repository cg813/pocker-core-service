import pytest

from uuid import uuid4
from rest_framework.reverse import reverse

from .helpers import create_user, create_currency, create_payment_provider
from payments.services.psp.fintech_cashier import get_fintech_cashier_redirect_url
from payments.services.psp.ensopay import get_ensopay_redirect_url


@pytest.mark.django_db
def test_get_fintech_cashier_redirect_url():
    currency = create_currency()
    user = create_user()
    payment_provider = create_payment_provider('fintech_cashier')

    url = get_fintech_cashier_redirect_url(user, payment_provider, currency, uuid4(), 20)

    assert url is not None


@pytest.mark.django_db
def test_fintechcashier_endpoint(api_client):
    create_currency()
    create_payment_provider('fintech_cashier')
    response = api_client.get(f"{reverse('deposit')}?amount=10&provider=fintech_cashier&currency=USD")

    assert response.status_code == 200
    assert 'url' in response.data


@pytest.mark.django_db
def test_get_ensopay_redirect_url():
    user = create_user()
    payment_provider = create_payment_provider('ensopay')

    url = get_ensopay_redirect_url(user, payment_provider,  uuid4(), 20)

    assert url is not None
