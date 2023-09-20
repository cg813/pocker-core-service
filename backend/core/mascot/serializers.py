from rest_framework import serializers
from .models import MascotBalanceLog, MascotPlayerBanks, MascotBanks, MascotSessions



class MascotBalanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MascotBalanceLog
        fields = '__all__'


class MascotPlayerBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = MascotPlayerBanks
        fields = "__all__"


class MascotBanksSerializer(serializers.ModelSerializer):
    class Meta:
        model = MascotBanks
        fields = "__all__"


class MascotSessionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MascotSessions
        fields = "__all__"
