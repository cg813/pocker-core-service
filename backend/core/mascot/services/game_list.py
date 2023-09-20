import requests
import json
import os

from requests.exceptions import HTTPError

from mascot.models import (MascotBanks, MascotPlayerBanks)
from games.models import (GameProvider, Game)
from games.serializers import (
    GameProviderSerializer, MascotGameListSerializer, GameSerializer)


class SendRequestMascot():
    def send_request(self, payload, url):
        self.headers = {'content-Type': 'application/json; charset=utf-8',
                        'Accept': 'application/json'}

        mascot_pem_file = os.environ.get("MASCOT_PEM_FILE")
        print(mascot_pem_file)
        try:
            res = requests.post(url, data=json.dumps(
                payload), verify=True, cert=f"{mascot_pem_file}", headers=self.headers)
        except HTTPError as http_err:
            raise http_err
        except Exception as err:
            raise err

        return res


class GetGameList():
    def __init__(self):
        self.gameProvider = GameProvider.objects.first_or_none(name='Mascot')
        if not self.gameProvider:
            mascot_requirements = MascotRequirements()
            self.gameProvider = mascot_requirements.create_mascot_provider()

        self.providerSerialize = GameProviderSerializer(self.gameProvider)
        self.url = self.providerSerialize.data['base_url']

        self.payload = {
            "jsonrpc": "2.0",
            "method": "Game.List",
            "id": 1920911592
        }

    def get_all_games(self):
        send_request_class = SendRequestMascot()
        res = send_request_class.send_request(self.payload, self.url)

        response_data = res.json()

        all_game_list = response_data['result']['Games']
        mascot_game_ids = []
        for single_game in all_game_list:
            mascot_game_ids.append(single_game['Id'])
            serialize_game = MascotGameListSerializer(single_game)
            if serialize_game.is_valid:
                check = Game.objects.filter(game_id=single_game['Id']).first()
                if check is None:
                    Game.objects.create(
                        game_id=single_game['Id'],
                        name=single_game['Name'],
                        description=single_game['Description'],
                        provider=single_game['SectionId'],
                        provider_id=self.gameProvider,
                        type=single_game['Type']
                    )

        games = self.gameProvider.game_set.all()
        for single_game in games:
            game_serialize = GameSerializer(single_game)
            if (len(list(filter(lambda x: x == game_serialize.data.get('game_id'), mascot_game_ids))) == 0):
                single_game.is_active = False
                single_game.save()


class MascotRequirements():

    def make_bank(self, url):

        payload = {
            "jsonrpc": "2.0",
            "method": "BankGroup.Set",
            "id": 1225625456,
            "params": {
                "Id": "main_usd_bank",
                "Currency": "USD"
            }
        }

        send_request_class = SendRequestMascot()
        res = send_request_class.send_request(payload, url)

        bank = MascotBanks.objects.create(
            name="main_usd_bank",
            currency="USD",
            is_default=True
        )

        return bank

    def connect_player_to_bank(self, url, player_name, player_id, bank_id, user, bank):

        payload = {
            "jsonrpc": "2.0",
            "method": "Player.Set",
            "id": 1928822491,
            "params": {
                "Id": f"{player_id}",
                "Nick": f"{player_name}",
                "BankGroupId": f"{bank_id}"
            }
        }

        send_request_class = SendRequestMascot()
        res = send_request_class.send_request(payload, url)

        MascotPlayerBanks.objects.create(
            player_id=user,
            bank_id=bank,
        )

        return True

    def create_mascot_provider(self):
        provider = GameProvider.objects.create(
            name="Mascot",
            description="Mascot Game Provider",
            base_url="https://api.mascot.games/v1/"
        )

        return provider

    def set_mascot_bonus(self, url, user_id):
        payload = {
            "jsonrpc": "2.0",
            "method": "Bonus.Set",
            "id": 1928822492,
            "params": {
                "Id": f"{user_id}"
            }
        }

        send_request_class = SendRequestMascot()
        res = send_request_class.send_request(payload, url)

        return f"{user_id}"
