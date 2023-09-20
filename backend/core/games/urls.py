from django.urls import path

from .views import (GetGames, GenerateGameToken, CheckUserToken, GameTransactionView,
                    MascotDemoGame, GameGetBalance, GetRoundDetails, MascotRealGame,
                    GameLikeManage, MascotFreeRound)

urlpatterns = [
    path('games/', GetGames.as_view({'get': 'list'})),
    path('games/<str:game_id>/', GetGames.as_view({'get': 'retrieve'})),
    path('game/like', GameLikeManage.as_view(), name='mange_game_like'),
    path('generate/token/<str:game_id>/', GenerateGameToken.as_view()),
    path('mascot/demo_game', MascotDemoGame.as_view(), name='mascot_demo_game'),
    path('mascot/real_game', MascotRealGame.as_view(), name='mascot_real_game'),
    path('mascot/free_round', MascotFreeRound.as_view(), name="mascot_free_round"),
    path('check/', CheckUserToken.as_view()),
    path('transaction/', GameTransactionView.as_view(), name='transaction'),
    path('get_balance/', GameGetBalance.as_view(), name='get_balance'),
    path('get_round_details/<str:game_id>/<str:round_id>/', GetRoundDetails.as_view(), name="get_round_detail"),
]
