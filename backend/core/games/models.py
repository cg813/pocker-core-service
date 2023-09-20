from django.db import models
from accounts.models import UserAccount
from uuid import uuid4


class GetOrNoneManager(models.Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def first_or_none(self, **kwargs):
        try:
            return self.filter(**kwargs).first()
        except self.model.DoesNotExist:
            return None


class Game(models.Model):
    """ CUSTOM GAME MODEL """
    game_id = models.CharField(max_length=200)
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    provider = models.CharField(max_length=100, null=True, blank=True)
    provider_id = models.ForeignKey(
        'games.GameProvider', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    base_url = models.CharField(max_length=500, null=True, blank=True)
    get_round_detail_url = models.CharField(max_length=500, null=True, blank=True)
    is_test = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    cover_image = models.ImageField(
        upload_to="game_cover_images", blank=True, null=True)
    cover_image_mobile = models.ImageField(
        upload_to="game_cover_images_mobile", blank=True, null=True)
    min_ante = models.FloatField(default=1)
    max_ante = models.FloatField(default=10)
    played_time = models.IntegerField(default=0)
    objects = GetOrNoneManager()

    def __str__(self):
        return self.name


class UserGameToken(models.Model):
    """ CUSTOM TOKEN MODEL  """
    token = models.UUIDField(default=uuid4)

    game = models.ForeignKey(
        Game,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    objects = GetOrNoneManager()

    def __str__(self):
        return f'{self.user.username} | {self.token}'


class GameProvider(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    base_url = models.CharField(max_length=200)

    objects = GetOrNoneManager()

    def __str__(self):
        return self.name


class UserGameLike(models.Model):

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    objects = GetOrNoneManager()

    def __str__(self):
        return f'{self.user.username} | {self.game.name}'
