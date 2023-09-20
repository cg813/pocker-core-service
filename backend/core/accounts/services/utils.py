import os
import uuid
import requests
from accounts.models import Wallet

from gcloud import storage
from oauth2client.service_account import ServiceAccountCredentials
from rest_framework.exceptions import ValidationError


def get_bucket():
    credentials_dict = {
        "type": "service_account",
        "client_id": os.environ.get('BUCKET_CLIENT_ID'),
        "client_email": os.environ.get('BUCKET_CLIENT_EMAIL'),
        "private_key_id": os.environ.get('BUCKET_PRIVATE_KEY_ID'),
        "private_key": os.environ.get('BUCKET_PRIVATE_KEY'),
    }

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        credentials_dict
    )
    client = storage.Client(credentials=credentials, project=os.environ.get('BUCKET_PROJECT_ID'))
    bucket = client.get_bucket(os.environ.get('BUCKET_NAME'))
    return bucket


def upload_to_bucket(file, bucket, filename):
    folder_name = os.environ.get('BUCKET_FOLDER_NAME')
    blob = bucket.blob(f'{folder_name}/{filename}', chunk_size=262144)
    blob.upload_from_string(file.file.read())


def path_and_rename(instance, filename):
    path = 'identification_images/'
    ext = filename.split('.')[-1]
    # set filename as random string
    filename = '{}.{}'.format(uuid.uuid4().hex, ext)
    # return the whole path to the file
    print(os.path.join(path, filename))
    return os.path.join(path, filename)


def validate_captcha_token(captcha_token):
    request_data = {
        'secret': '6LcSqdAeAAAAAPdXbTxPO7kKAz45DsUwMzVMyeve',
        'response': captcha_token
    }

    url = 'https://www.google.com/recaptcha/api/siteverify'
    response = requests.post(url, data=request_data).json()

    if not response.get('success'):
        raise ValidationError({'message': 'wrong captcha token'})


def get_or_update_notify_bonus(wallet: Wallet):
    if wallet.notify_bonus is True:
        wallet.notify_bonus = False
        wallet.save()
        return True
    return False
