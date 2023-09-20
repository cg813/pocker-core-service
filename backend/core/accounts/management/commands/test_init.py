import os
from django.core.management.base import BaseCommand
from accounts.models import UserAccount, Wallet, Currency
from games.models import Game


class Command(BaseCommand):
    def handle(self, *args, **options):
        test_game_id = os.environ.get("TEST_GAME_ID", "617bebafdc59c1a17fbcebb4")
        test_user = UserAccount.objects.create_superuser(username="test", email="testuser@gmail.com",
                                                         password="testuser123")
        currency = Currency.objects.create(iso="USD", symbol="$", full_name="test", is_main=True)
        Wallet.objects.create(user=test_user, currency=currency, balance=10000000, active=True)
        wallets = Wallet.objects.all()
        for wallet in wallets:
            if wallet.balance < 100:
                wallet.delete()
        Game.objects.create(game_id=test_game_id, name="test game",
                            base_url="http://casino-poker-backend-service:8001/casinopoker/get/game/url", is_active=True)
