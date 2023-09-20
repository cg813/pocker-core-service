from django.contrib import admin
from .models import (Game, UserGameToken, GameProvider)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    change_list_template = 'games_change_list.html'

    def get_readonly_fields(self, request, obj):
        if request.user.is_admin or request.user.is_superuser:
            return []
        return ['game_id', 'name', 'base_url', 'cover_image', 'min_ante', 'max_ante', 'is_test']


admin.site.register(UserGameToken)
admin.site.register(GameProvider)
