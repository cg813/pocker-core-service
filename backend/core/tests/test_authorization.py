import pytest
import base64
import json

from rest_framework import status
from rest_framework.reverse import reverse

from accounts.models import UserAccount
from .helpers import create_user

email = 'test@mima-poker.com'
password = 'Test1234@'


def log_in(client):
    response = client.post(reverse('log_in'), data={
        'email': email,
        'password': password
    })
    access_token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'JWT {access_token}')
    return client


@pytest.mark.django_db
def test_user_can_sign_up(monkeypatch, client):
    monkeypatch.setattr('accounts.services.utils.validate_captcha_token', lambda token: print(token))
    response = client.post(reverse('sign_up'), data={
        'username': 'test_username',
        'email': 'test@gmail.com',
        'password': password,
        'confirm_password': password,
        'captcha_token': 'blablabla'
    })
    user = UserAccount.objects.last()
    assert status.HTTP_201_CREATED == response.status_code
    assert response.data['username'] == user.username
    assert response.data['email'] == user.email


@pytest.mark.django_db
def test_user_can_log_in(client):
    user = create_user()
    response = client.post(reverse('log_in'), data={
        'email': user.email,
        'password': password
    })
    # Parse payload data from access token
    access = response.data['access']
    header, payload, signature = access.split('.')
    decoded_payload = base64.b64decode(f'{payload}==')
    payload_data = json.loads(decoded_payload)

    assert status.HTTP_200_OK == response.status_code
    assert 'refresh' in response.data
    assert payload_data['user_id'] == user.id
    assert payload_data['username'] == user.username


@pytest.mark.django_db
def test_login(api_client):
    response = api_client.post(reverse('log_in'), data={
        'email': email,
        'password': password
    })

    assert 'access' in response.data
    assert 'refresh' in response.data


@pytest.mark.django_db
def test_logout(api_client):
    client = log_in(api_client)
    response = client.get(reverse('log_out'))

    user = UserAccount.objects.get_or_none(email='test@mima-poker.com')

    assert response.status_code == 200
    assert user.logged_out is True


@pytest.mark.django_db
def test_logout_status_on_login(api_client):
    client = log_in(api_client)
    client.get(reverse('log_out'))
    client = log_in(api_client)

    user = UserAccount.objects.get_or_none(email='test@mima-poker.com')

    assert user.logged_out is False
