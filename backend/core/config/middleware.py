from urllib.parse import parse_qs

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.auth import AuthMiddleware
from channels.db import database_sync_to_async
from channels.sessions import CookieMiddleware, SessionMiddleware
from rest_framework_simplejwt.tokens import AccessToken

from game.models import Game


User = get_user_model()


@database_sync_to_async
def get_user(scope):
    print('gjkghjgh')
    close_old_connections()
    query_string = parse_qs(scope['query_string'].decode())
    token = query_string.get('token')
    if not token:
        return AnonymousUser()
    try:
        access_token = AccessToken(token[0])
        user = User.objects.get(id=access_token['user_id'])
    except Exception as exception:
        return AnonymousUser()
    if not user.is_active:
        return AnonymousUser()
    return user


@database_sync_to_async
def get_game(scope):
    close_old_connections()
    query_string = parse_qs(scope['query_string'].decode())
    game_id = query_string.get('game_id')
    if not game_id:
        return None
    try:
        game = Game.objects.get(game_id=game_id)
    except Game.DoesNotExist:
        return None
    return game


class TokenAuthMiddleware(AuthMiddleware):
    async def resolve_scope(self, scope):
        scope['user']._wrapped = await get_user(scope)


def TokenAuthMiddlewareStack(inner):
    return CookieMiddleware(SessionMiddleware(TokenAuthMiddleware(inner)))
