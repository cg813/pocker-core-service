import os
from re import U
import requests
import json

from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from requests.exceptions import HTTPError
from collections import defaultdict


from .models import (Game, UserGameToken, GameProvider, UserGameLike)
from .serializers import (CheckUserTokenSerializer, GameGetBalanceSerializer, GameSerializer,
                          GameTransactionRequestSerializer, GameProviderSerializer)
from .services.game_transactions import TransactionManager
from .services.utils import get_balance

from accounts.models import Wallet
from accounts.serializers import (WalletSerializer, UserDataSerializer)
from mascot.models import (MascotBanks, MascotPlayerBanks, MascotSessions)
from mascot.serializers import MascotBanksSerializer
from mascot.services.game_list import (MascotRequirements, SendRequestMascot)


class GetGames(viewsets.ViewSet):

    @staticmethod
    def list(request):
        user = request.user
        user_serializer = UserDataSerializer(user)
        all_likes = []
        if user_serializer.data.get('id') != None:
            user_game_likes = UserGameLike.objects.filter(user=user).all()
            for one_game in user_game_likes:
                get_game = one_game.game
                get_game_serialize = GameSerializer(get_game)
                all_likes.append(get_game_serialize.data.get('game_id'))

        limit = True
        if not request.GET.get('limit'):
            limit = False

        games = Game.objects.filter(is_test=False, is_active=True)
        serializer = GameSerializer(games, many=True)

        groupedGames = defaultdict(list)
        for singleGame in serializer.data:
            if (len(list(filter(lambda x: x == singleGame.get('game_id'), all_likes))) > 0):
                singleGame['is_favorite'] = True
            else:
                singleGame['is_favorite'] = False
            if limit:
                if len(groupedGames[singleGame['type']]) < int(request.GET.get('limit')):
                    groupedGames[singleGame['type']].append(singleGame)
            else:
                groupedGames[singleGame['type']].append(singleGame)

        return Response(groupedGames, status=status.HTTP_200_OK)

    @staticmethod
    def retrieve(request, game_id):
        game = Game.objects.filter(
            game_id=game_id, is_test=False, is_active=True).first()
        serializer = GameSerializer(game)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GenerateGameToken(APIView):

    @staticmethod
    def get(request):
        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def post(request, game_id):
        game = Game.objects.get_or_none(game_id=game_id)
        if game:
            user_token = UserGameToken.objects.create(
                game=game, user=request.user)
            headers = {'HOST': "backend:8000",
                       'API-KEY': os.environ.get("MERCHANT_API_KEY")}
            url = f'{game.base_url}/?game_id={game.game_id}&user_token={user_token.token}'
            r = requests.get(url, headers=headers)
            return Response(r.json(), status=r.status_code)
        return Response(status=status.HTTP_404_NOT_FOUND)


class CheckUserToken(APIView):
    authentication_classes = ()

    @staticmethod
    def post(request):
        serializer = CheckUserTokenSerializer(data=request.data)
        if serializer.is_valid():
            user_token = serializer.data.get('launch_token')
            token = UserGameToken.objects.get_or_none(
                token=user_token, active=True)
            wallet = Wallet.objects.select_related(
                'currency').get(user=token.user, active=True)
            data = {
                "token": user_token,
                "total_balance": get_balance(wallet),
                "currency": wallet.currency.iso,
                "user_name": token.user.username,
                "user_id": token.user.id,
                "status": 'Ok',
                "is_dealer": token.user.is_dealer,
            }
            if token:
                return Response(data=data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)


class GameTransactionView(APIView):

    @staticmethod
    def post(request):
        print(request.data)
        serializer = GameTransactionRequestSerializer(data=request.data)

        if serializer.is_valid():
            print(serializer.data)
            transaction_manager = TransactionManager(serializer.data)
            transaction_status, message = transaction_manager.make_transaction()
            print(transaction_status, message)
            return Response(data=message, status=transaction_status)

        return Response(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class GameGetBalance(APIView):

    @staticmethod
    def post(request):
        serializer = GameGetBalanceSerializer(data=request.data)

        if serializer.is_valid():
            print(serializer.data)
            token = UserGameToken.objects.get_or_none(token=serializer.data.get('token'),
                                                      active=True)
            wallet = Wallet.objects.get_or_none(
                user=token.user, currency__iso=serializer.data.get('currency'))
            message = {
                'total_balance': wallet.balance + wallet.bonus_balance,
                'currency': wallet.currency.iso,
                'status': 'Ok'
            }
            return Response(data=message, status=status.HTTP_200_OK)
        return Response({'status': 'Failed'}, status=status.HTTP_200_OK)


class GetRoundDetails(APIView):
    permission_classes = (IsAuthenticated, )

    @staticmethod
    def get(request, game_id, round_id):
        game: Game = Game.objects.get_or_none(game_id=game_id)
        if game:
            headers = {'HOST': "backend:8000",
                       'API-KEY': os.environ.get("MERCHANT_API_KEY")}
            payload = {
                "game_id": game_id,
                "round_id": round_id,
                "user_id": request.user.id
            }
            url = f'{game.get_round_detail_url}'
            r = requests.post(url, json=payload, headers=headers)
            return Response(r.json(), status=r.status_code)
        return Response(status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def post(request):
        return Response(status=status.HTTP_200_OK)


class HealthCheck(APIView):
    permission_classes = ()
    authentication_classes = ()

    @staticmethod
    def get(request):
        return Response({"OK": 200}, status=status.HTTP_200_OK)


class MascotDemoGame(APIView):
    def __init__(self):
        self.mascot_requirements = MascotRequirements()

    def get(self, request):
        if not request.GET.get('game_id'):
            return Response({"message": "game_id field is required"}, status=status.HTTP_400_BAD_REQUEST)

        lang = 'en'
        if request.GET.get("lang"):
            lang = request.GET.get("lang")

        game = Game.objects.first_or_none(game_id=request.GET.get(
            'game_id'), is_active=True, is_test=False)

        if not game:
            return Response({"message": "game with this id not found"}, status=status.HTTP_404_NOT_FOUND)

        game_serialize = GameSerializer(game)
        game_provider = GameProvider.objects.first_or_none(name='Mascot')

        if not game_provider:
            game_provider = self.mascot_requirements.create_mascot_provider()

        provider_serialize = GameProviderSerializer(game_provider)

        url = provider_serialize.data['base_url']
        bank = MascotBanks.objects.first_or_none(
            name="main_usd_bank", currency="USD")
        if not bank:
            self.mascot_requirements.make_bank(url)

        payload = {
            "jsonrpc": "2.0",
            "method": "Session.CreateDemo",
            "id": 321864203,
            "params": {
                "BankGroupId": "main_usd_bank",
                "GameId": game_serialize.data['game_id'],
                "StartBalance": 10000,
                "RestorePolicy": "Restore",
                "Params": {
                    "language": f"{lang}"
                }
            }
        }

        send_request_class = SendRequestMascot()
        res = send_request_class.send_request(payload, url)
        data = res.json()

        if isinstance(game_serialize.data.get('played_time'), int):
            game.played_time += 1
        else:
            game.played_time = 0

        game.save()

        return Response(data['result'], status=status.HTTP_200_OK)


class MascotRealGame(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        self.mascot_requirements = MascotRequirements()

    def get(self, request):

        if not request.GET.get('game_id'):
            return Response({"message": "game_id field is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not request.GET.get('type'):
            return Response({"message": "type field is required"}, status=status.HTTP_400_BAD_REQUEST)

        lang = 'en'
        if request.GET.get("lang"):
            lang = request.GET.get("lang")

        type = request.GET.get('type')
        type = type.replace('_', ' ')
        game = Game.objects.first_or_none(game_id=request.GET.get(
            'game_id'), is_active=True, is_test=False)
        if not game:
            return Response({"message": "game with this id not found"}, status=status.HTTP_404_NOT_FOUND)
        game_serialize = GameSerializer(game)
        game_provider = GameProvider.objects.first_or_none(name='Mascot')

        if not game_provider:
            game_provider = self.mascot_requirements.create_mascot_provider()

        provider_serialize = GameProviderSerializer(game_provider)

        url = provider_serialize.data['base_url']
        user = request.user

        user_serializer = UserDataSerializer(user)

        wallet = Wallet.objects.filter(user=user, currency__iso='USD').first()

        if not wallet:
            return Response({"message": "user dont have wallet"},
                            status=status.HTTP_404_NOT_FOUND)

        bank = MascotBanks.objects.first_or_none(
            name="main_usd_bank", currency="USD")
        if not bank:
            bank = self.mascot_requirements.make_bank(url)

        bank_serializer = MascotBanksSerializer(bank)
        player_bank = MascotPlayerBanks.objects.first_or_none(player_id=user_serializer.data['id'],
                                                              bank_id=bank_serializer.data['id'])
        player_name = f"{user_serializer.data['first_name']} {user_serializer.data['last_name']}"

        if not player_bank:
            self.mascot_requirements.connect_player_to_bank(provider_serialize.data['base_url'], player_name, user_serializer.data['id'],
                                                            bank_serializer.data['name'], user, bank)

        url = provider_serialize.data['base_url']

        user_mascot_session = MascotSessions.objects.filter(
            user_id=user_serializer.data['id']).first()

        if user_mascot_session:
            user_mascot_session.session_id = 'N/A'
            user_mascot_session.type = type
            user_mascot_session.save()

        else:
            user_mascot_session = MascotSessions.objects.create(
                session_id='N/A',
                type=type,
                user=user
            )

        print(lang)

        payload = {
            "jsonrpc": "2.0",
            "method": "Session.Create",
            "id": 321864203,
            "params": {
                "PlayerId": f"{user_serializer.data['id']}",
                "GameId": f"{game_serialize.data['game_id']}",
                "RestorePolicy": "Restore",
                "Params": {
                    "language": f"{lang}"
                }
            }
        }

        send_request_class = SendRequestMascot()
        res = send_request_class.send_request(payload, url)

        data = res.json()

        print(data)

        if data.get('error'):
            return Response(data.get('error'), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if isinstance(game_serialize.data.get('played_time'), int):
            game.played_time += 1
        else:
            game.played_time = 0

        game.save()

        user_mascot_session.session_id = data['result']['SessionId']
        user_mascot_session.save()

        return Response(data['result'], status=status.HTTP_200_OK)


class MascotFreeRound(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        self.mascot_requirements = MascotRequirements()

    def get(self, request):

        if not request.GET.get('game_id'):
            return Response({"message": "game_id field is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not request.GET.get('type'):
            return Response({"message": "type field is required"}, status=status.HTTP_400_BAD_REQUEST)

        type = request.GET.get('type')
        type = type.replace('_', ' ')
        game = Game.objects.first_or_none(game_id=request.GET.get(
            'game_id'), is_active=True, is_test=False)
        if not game:
            return Response({"message": "game with this id not found"}, status=status.HTTP_404_NOT_FOUND)
        game_serialize = GameSerializer(game)
        game_provider = GameProvider.objects.first_or_none(name='Mascot')

        if not game_provider:
            game_provider = self.mascot_requirements.create_mascot_provider()

        provider_serialize = GameProviderSerializer(game_provider)

        url = provider_serialize.data['base_url']
        user = request.user

        user_serializer = UserDataSerializer(user)

        wallet = Wallet.objects.filter(user=user, currency__iso='USD').first()

        if not wallet:
            return Response({"message": "user dont have wallet"},
                            status=status.HTTP_404_NOT_FOUND)

        bank = MascotBanks.objects.first_or_none(
            name="main_usd_bank", currency="USD")
        if not bank:
            bank = self.mascot_requirements.make_bank(url)

        bank_serializer = MascotBanksSerializer(bank)
        player_bank = MascotPlayerBanks.objects.first_or_none(player_id=user_serializer.data['id'],
                                                              bank_id=bank_serializer.data['id'])
        player_name = f"{user_serializer.data['first_name']} {user_serializer.data['last_name']}"

        if not player_bank:
            self.mascot_requirements.connect_player_to_bank(provider_serialize.data['base_url'], player_name, user_serializer.data['id'],
                                                            bank_serializer.data['name'], user, bank)

        url = provider_serialize.data['base_url']

        user_mascot_session = MascotSessions.objects.filter(
            user_id=user_serializer.data['id']).first()

        if user_mascot_session:
            user_mascot_session.session_id = 'N/A'
            user_mascot_session.type = type
            user_mascot_session.save()

        else:
            user_mascot_session = MascotSessions.objects.create(
                session_id='N/A',
                type=type,
                user=user
            )

        bonus_id = self.mascot_requirements.set_mascot_bonus(
            url, user_serializer.data.get('id'))

        payload = {
            "jsonrpc": "2.0",
            "method": "Session.Create",
            "id": 321864203,
            "params": {
                "PlayerId": f"{user_serializer.data['id']}",
                "GameId": f"{game_serialize.data['game_id']}",
                "BonusId": f"{bonus_id}"
            }
        }

        send_request_class = SendRequestMascot()
        res = send_request_class.send_request(payload, url)

        # headers = {'content-Type': 'application/json; charset=utf-8',
        #            'Accept': 'application/json'}

        # try:
        #     res = requests.post(url, data=json.dumps(payload), verify=True, cert='./mascot/ssl/apikey.pem',
        #                         headers=headers)

        # except HTTPError as http_err:
        #     raise http_err
        # except Exception as err:
        #     raise err
        data = res.json()

        if data.get('error'):
            return Response(data.get('error'), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if isinstance(game_serialize.data.get('played_time'), int):
            game.played_time += 1
        else:
            game.played_time = 0

        game.save()

        user_mascot_session.session_id = data['result']['SessionId']
        user_mascot_session.save()

        return Response(data['result'], status=status.HTTP_200_OK)


class GameLikeManage(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        game = Game.objects.first_or_none(game_id=request.data.get('game_id'))
        user = request.user

        if not game:
            return Response({"message": "game Id is not valid"}, status=status.HTTP_404_NOT_FOUND)

        user_game_like = UserGameLike.objects.first_or_none(
            game=game, user=user)

        if user_game_like:
            user_game_like.delete()
            return Response({"message": "disliked"}, status=status.HTTP_201_CREATED)
        else:

            UserGameLike.objects.create(
                game=game,
                user=user
            )

            return Response({"message": "liked"}, status=status.HTTP_201_CREATED)
