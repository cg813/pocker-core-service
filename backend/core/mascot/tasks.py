
import logging

from celery import shared_task

from .services.game_list import GetGameList
logger = logging.getLogger('django')


@shared_task
def save_mascot_game_list():

    get_game_list = GetGameList()
    get_game_list.get_all_games()
    logger.info('All Mascot Games Updated')
