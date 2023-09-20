import uuid

from django.utils import timezone
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from accounts.models import Transaction, Wallet
from .helpers import setup_data


@pytest.mark.django_db
def test_user_bet_wrong_schema(client):
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data()

    response = client.post(reverse('transaction'), data={
        'amount': 110,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    assert status.HTTP_400_BAD_REQUEST == response.status_code


@pytest.mark.django_db
def test_user_bet_wrong_user_token(client):
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data()

    response = client.post(reverse('transaction'), data={
        'token': uuid.uuid4(),
        'amount': 110,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Failed'
    assert response.data.get('error_description') == 'token is not valid'
    assert wallet.balance == 100


@pytest.mark.django_db
def test_user_unsupported_operation(client):
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data()

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': 110,
        'transaction_type': 'split',
        'external_id': game_transaction_id,
        'round_id': game_round
    })
    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Failed'
    assert response.data.get('error_description') == 'unsupported operation'
    assert wallet.balance == 100


@pytest.mark.django_db
def test_user_bet_insufficient_funds(client):
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data()

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': 110,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Failed'
    assert response.data.get('error_description') == 'insufficient funds'
    assert response.data.get('total_balance') == wallet.balance


@pytest.mark.django_db
def test_user_bet_sufficient_funds(client):
    amount = 10
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data()

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    transaction = Transaction.objects.get(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='bet',
        transaction_status='success'
    )

    wallet = Wallet.objects.get(user=user, currency=wallet.currency)

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Ok'
    assert response.data.get('total_balance') == wallet.balance
    assert transaction.amount == amount


@pytest.mark.django_db
def test_user_bet_sufficient_fund_but_logged_out(client):
    amount = 10
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data()

    user.logged_out = True
    user.save()

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Failed'
    assert response.data.get('error_description') == 'user is logged out'


@pytest.mark.django_db
def test_user_win_when_logged_out(client):
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()
    amount = 10

    user, game, user_token, wallet = setup_data()

    user.logged_out = True
    user.save()

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'win',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    transaction = Transaction.objects.get(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='win',
        transaction_status='success'
    )

    wallet = Wallet.objects.get(user=user, currency=wallet.currency)

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Ok'
    assert response.data.get('total_balance') == wallet.balance
    assert transaction.amount == amount


@pytest.mark.django_db
def test_user_win(client):
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()
    amount = 10

    user, game, user_token, wallet = setup_data()

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'win',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    transaction = Transaction.objects.get(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='win',
        transaction_status='success'
    )

    wallet = Wallet.objects.get(user=user, currency=wallet.currency)

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Ok'
    assert response.data.get('total_balance') == wallet.balance
    assert transaction.amount == amount


@pytest.mark.django_db
def test_user_bonus_bet(client):
    amount = 10
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data(bonus=True)

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    transaction = Transaction.objects.get(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='bonus_bet',
        transaction_status='success'
    )

    wallet = Wallet.objects.get(user=user, currency=wallet.currency)

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Ok'
    assert response.data.get('total_balance') == wallet.balance + wallet.bonus_balance
    assert transaction.amount == amount


@pytest.mark.django_db
def test_user_combined_bet(client):
    amount = 40
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data(bonus=True)

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    bonus_transaction = Transaction.objects.get(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='bonus_bet',
        transaction_status='success'
    )

    real_transaction = Transaction.objects.get(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='bet',
        transaction_status='success'
    )

    wallet = Wallet.objects.get(user=user, currency=wallet.currency)

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Ok'
    assert response.data.get('total_balance') == wallet.balance + wallet.bonus_balance
    assert bonus_transaction.amount == wallet.bonus_bet
    assert real_transaction.amount == amount - wallet.bonus_bet


@pytest.mark.django_db
def test_bonus_win(client):
    amount = 10
    winning_amount = 10
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data(bonus=True)

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': winning_amount,
        'transaction_type': 'win',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    transaction = Transaction.objects.get(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='bonus_win',
        transaction_status='success'
    )

    wallet = Wallet.objects.get(user=user, currency=wallet.currency)

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Ok'
    assert response.data.get('total_balance') == wallet.balance + wallet.bonus_balance
    assert transaction.amount == winning_amount
    assert transaction.balance == wallet.bonus_balance - winning_amount
    assert wallet.bonus_bet == 0
    assert wallet.amount_wagered == amount


@pytest.mark.django_db
def test_combined_win(client):
    amount = 10
    winning_amount = 30
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data(bonus=True)

    bet_response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    wallet_before_win = Wallet.objects.get(user=user, currency=wallet.currency)

    win_response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': winning_amount,
        'transaction_type': 'win',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    bonus_transaction = Transaction.objects.get(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='bonus_win',
        transaction_status='success'
    )

    real_transaction = Transaction.objects.get(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='win',
        transaction_status='success'
    )

    wallet_after_win = Wallet.objects.get(user=user, currency=wallet.currency)

    assert status.HTTP_200_OK == win_response.status_code
    assert bet_response.data.get('status') == 'Ok'
    assert bet_response.data.get('total_balance') == wallet_before_win.balance + wallet_before_win.bonus_balance
    assert win_response.data.get('status') == 'Ok'
    assert win_response.data.get('total_balance') == wallet_after_win.balance + wallet_after_win.bonus_balance

    assert bonus_transaction.amount == wallet_before_win.bonus_bet
    assert real_transaction.amount == winning_amount - wallet_before_win.bonus_bet

    assert wallet_after_win.bonus_bet == 0
    assert wallet_after_win.amount_wagered == amount


@pytest.mark.django_db
def test_bonus_reset(client):
    amount = 10
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data(bonus=True)

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'reset',
        'external_id': game_transaction_id,
        'round_id': game_round
    })

    transaction = Transaction.objects.get(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='bonus_reset',
        transaction_status='success'
    )

    wallet = Wallet.objects.get(user=user, currency=wallet.currency)

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Ok'
    assert response.data.get('total_balance') == wallet.balance + wallet.bonus_balance
    assert transaction.amount == amount
    assert wallet.bonus_bet == 0
    assert wallet.amount_wagered == 0


@pytest.mark.django_db
def test_expired_bonus(client):
    amount = 10
    game_round = uuid.uuid4()
    game_transaction_id = uuid.uuid4()

    user, game, user_token, wallet = setup_data(bonus=True)

    # MAKE BONUS EXPIRE
    wallet.bonus_expiration_date = timezone.now() + timezone.timedelta(days=-1)
    wallet.save()

    response = client.post(reverse('transaction'), data={
        'token': user_token.token,
        'amount': amount,
        'transaction_type': 'bet',
        'external_id': game_transaction_id,
        'round_id': game_round,
    })

    transaction = Transaction.objects.get_or_none(
        user=user,
        game=game,
        game_round=game_round,
        transaction_type='bonus_reset',
        transaction_status='success'
    )

    wallet = Wallet.objects.get(user=user, currency=wallet.currency)

    assert status.HTTP_200_OK == response.status_code
    assert response.data.get('status') == 'Ok'
    assert response.data.get('total_balance') == wallet.balance
    assert transaction is None
    assert wallet.bonus_balance == 0
    assert wallet.bonus_bet == 0
    assert wallet.amount_wagered == 0
    assert wallet.bonus_expiration_date is None
    assert wallet.bonus_requirement is None


@pytest.mark.django_db
def test_get_balance(client):
    _, _, user_token, wallet = setup_data()

    response = client.post(reverse('get_balance'), data={
        'token': user_token.token,
        'currency': wallet.currency.iso,
    })

    data = response.json()

    assert status.HTTP_200_OK == response.status_code
    assert data.get('status') == 'Ok'
    assert data.get('currency') == wallet.currency.iso
    assert data.get('total_balance') == wallet.balance + wallet.bonus_balance
