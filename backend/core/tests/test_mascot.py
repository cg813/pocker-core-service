from email import header
import keyword
from wsgiref.headers import Headers
import pytest
import requests

from rest_framework.reverse import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from .helpers import (make_bank_mascot, make_provider_mascot, create_user)
from mascot.serializers import MascotBanksSerializer
from games.serializers import (GameProviderSerializer, GameSerializer)
from games.models import GameProvider
from mascot.models import MascotBanks
from mascot.services.game_list import (GetGameList, MascotRequirements)
from accounts.models import (Currency, Wallet)


@pytest.mark.django_db
def test_get_mascot_game_list(client):
    get_game_list_class = GetGameList()

    get_game_list_class.get_all_games()

    provider = GameProvider.objects.first_or_none(name="Mascot")

    slot_game = provider.game_set.filter(type='slots').first()

    assert provider != None
    assert slot_game != None


@pytest.mark.django_db
def test_creating_mascot_bank():
    make_provider_mascot()
    provider = GameProvider.objects.first_or_none(name="Mascot")
    provider_serialize = GameProviderSerializer(provider)
    mascot_requirements = MascotRequirements()
    url = provider_serialize.data.get('base_url')
    make_mascot_bank = mascot_requirements.make_bank(url)

    mascot_bank_serialize = MascotBanksSerializer(make_mascot_bank)

    assert mascot_bank_serialize.data.get("name") == "main_usd_bank"


@pytest.mark.django_db
def test_save_mascot_bank():
    bank = make_bank_mascot()

    bank = MascotBanks.objects.filter(name="main_usd_bank").first()

    assert bank != None


@pytest.mark.django_db
def test_start_demo_game(client):
    get_game_list_class = GetGameList()

    get_game_list_class.get_all_games()

    provider = GameProvider.objects.first_or_none(name="Mascot")

    slot_game = provider.game_set.filter(type='slots').first()

    slot_game.is_active = True
    slot_game.save()

    game_serialize = GameSerializer(slot_game)

    request = client.get(
        "/api/games/mascot/demo_game?game_id=" + game_serialize.data.get('game_id'))

    assert request.status_code == 200


# @pytest.mark.django_db
# def test_start_real_game(client):
#     user = create_user()

#     currency = Currency.objects.create(
#         iso="USD", symbol="$", full_name="test", is_main=True)
#     Wallet.objects.create(user=user, currency=currency,
#                           balance=10000000, active=True)

#     refresh = RefreshToken.for_user(user)
#     client.credentials(HTTP_AUTHORIZATION=f'JWT {refresh.access_token}')

#     get_game_list_class = GetGameList()

#     get_game_list_class.get_all_games()

#     provider = GameProvider.objects.first_or_none(name="Mascot")

#     slot_game = provider.game_set.filter(type='slots').first()

#     slot_game.is_active = True
#     slot_game.save()

#     game_serialize = GameSerializer(slot_game)

#     request = client.get('/api/games/mascot/real_game?game_id='+game_serialize.data.get(
#         'game_id')+'&type=with_bonus')

#     assert request.status_code == 200
