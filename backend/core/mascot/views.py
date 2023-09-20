from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from mascot.services.game_list import GetGameList


class AllTests(APIView):
    def get(self, request):
        game_list_class = GetGameList()
        game_list_class.get_all_games()

        return Response({"success": True}, status=status.HTTP_200_OK)
