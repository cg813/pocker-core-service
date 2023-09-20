import httpx
from celery import shared_task


@shared_task
def s2s_send_transaction(url, data):
    """ SENDING s2s transaction """
    response = httpx.post(url, data=data, timeout=15)
    print(response.content)
