import uuid

from django.utils import timezone

from accounts.models import Currency, UserAccount, Wallet
from payments.models import PaymentProvider, PaymentMethod
from games.models import Game, UserGameToken, GameProvider
from bonus.models import Bonus
from mascot.models import MascotBanks


def create_currency():
    currency = Currency.objects.create(
        iso='USD',
        symbol='$',
        full_name='united states dollar',
        divider=1,
        is_main=True
    )

    return currency


def create_user():
    user = UserAccount.objects.create_user(
        username='testuser',
        email='test@mima-poker.com',
        password='Test1234@',
    )
    user.is_active = True
    user.save()

    return user


def update_balance(user, currency):
    wallet = Wallet.objects.get(user=user, currency=currency)
    wallet.balance = 100
    wallet.save()

    return wallet


def create_game(game_id, name):
    return Game.objects.create(
        game_id=game_id,
        name=name
    )


def create_deposit_bonus(game):
    bonus = Bonus.objects.create(
        name='deposit_bonus',
        amount=30,
        wager_number=0,
        active_from=timezone.now(),
        active_to=(timezone.now() + timezone.timedelta(days=30)),
        expiration_time_days=10,
        games=game,
        is_deposit_bonus=True,
        deposit_amount=100,
        created_at=timezone.now()
    )
    return bonus


def update_bonus_balance(wallet: Wallet, bonus):
    wallet.bonus_expiration_date = timezone.now() + timezone.timedelta(days=30)
    wallet.bonus_balance = 30
    wallet.bonus_requirement = bonus
    wallet.save()
    return wallet


def create_user_game_token(game, user):
    return UserGameToken.objects.create(
        game=game,
        user=user,
    )


def setup_data(bonus=False):
    currency = create_currency()
    user = create_user()
    wallet = update_balance(user, currency)
    game = create_game(uuid.uuid4(), 'GAME1')
    user_game_token = create_user_game_token(game, user)

    if bonus:
        deposit_bonus = create_deposit_bonus(game)
        wallet = update_bonus_balance(wallet, deposit_bonus)

    return user, game, user_game_token, wallet


def create_payment_provider(name):
    payment_method = PaymentMethod.objects.create(
        name='visa',
        is_active=True
    )

    payment_provider = PaymentProvider.objects.create(
        name=name,
        test_sign_key='123',
        prod_sign_key='123',
        is_active=True,


    )
    if name == 'ensopay':
        payment_provider.test_endpoint = 'https://app.ensopay.com/api'
        payment_provider.gateway_number = '09874'

    payment_provider.payment_methods.add(payment_method, )
    payment_provider.save()

    return payment_provider


# from here all helpers are related to mascot
def make_mascot_casino_game(provider):
    game = Game.objects.create(
        game_id="holdem_mg",
        name="Casino Hold'em",
        description="Card Games",
        provider='mascot',
        provider_id=provider,
        type="casino",
        is_test=False,
        is_active=True,
    )

    return game


def make_mascot_slot_game(provider):
    game = Game.objects.create(
        game_id="cleopatras_gems_rockways",
        name="Cleopatra's Gems Rockways",
        description="6*6 rockways, avalanche, Free",
        provider='mascot',
        provider_id=provider,
        type="slots",
        is_test=False,
        is_active=True
    )

    return game


def make_provider_mascot():
    game_provider = GameProvider.objects.create(
        name='Mascot',
        description="this is Mascot provider",
        base_url="https://api.mascot.games/v1/"
    )

    return game_provider


def make_game_mascot():
    provider = make_provider_mascot()
    game_slot = make_mascot_slot_game(provider)
    game_casino = make_mascot_casino_game(provider)

    return game_slot, game_casino


def make_bank_mascot():
    bank = MascotBanks.objects.create(
        name="main_usd_bank",
        currency="USD",
        is_default=True
    )

    return bank
