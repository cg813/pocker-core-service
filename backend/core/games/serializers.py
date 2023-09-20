from rest_framework import serializers

from .models import (Game, GameProvider, UserGameLike)


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"


class MascotGameListSerializer(serializers.Serializer):
    Id = serializers.CharField(),
    Name = serializers.CharField(),
    Description = serializers.CharField(),
    SectionId = serializers.CharField(),
    Type = serializers.CharField(),


class GameTransactionRequestSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    amount = serializers.FloatField()
    transaction_type = serializers.CharField(max_length=50)
    external_id = serializers.CharField()
    round_id = serializers.CharField()


class GameProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameProvider
        fields = "__all__"


class GameGetBalanceSerializer(serializers.Serializer):
    token = serializers.CharField()
    currency = serializers.ChoiceField(['USD', 'ETH', 'BTC', 'EUR'])


class CheckUserTokenSerializer(serializers.Serializer):
    launch_token = serializers.CharField()


class UserGameLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGameLike
        fields = "__all__"
