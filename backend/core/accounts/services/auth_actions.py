from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from typing import Union

from accounts.models import UserAccount
from .tokens import account_activation_token


def activate_user(uid64: str, token: str) -> Union[bool, None]:
    """ function for activating user:
        if does not exists we will return False
        or token is not valid(expired) we will return also False.
     """
    try:
        uid = force_text(urlsafe_base64_decode(uid64))
        user = UserAccount.objects.get_or_none(id=uid)
    except(TypeError, ValueError, OverflowError):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return True


def reset_password(uid64: str, token: str, password: str) -> Union[bool, None]:
    """ FUNCTION FOR RESETTING THE PASSWORD """
    try:
        uid = force_text(urlsafe_base64_decode(uid64))
        user = UserAccount.objects.get_or_none(id=uid)
    except(TypeError, ValueError, OverflowError):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.set_password(password)
        user.save()
        return True
