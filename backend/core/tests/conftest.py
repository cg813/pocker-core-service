import pytest

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import (UserAccount)


@pytest.fixture
def api_client():
    user = UserAccount.objects.create_user(
        username='test',
        email='test@mima-poker.com',
        password='Test1234@'
    )
    user.is_active = True
    user.save()

    client = APIClient()

    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'JWT {refresh.access_token}')

    return client


@pytest.fixture
def client():
    client = APIClient()
    return client
