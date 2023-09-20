from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string

from celery import shared_task
import os

from .models import UserAccount
from accounts.services.tokens import account_activation_token


@shared_task
def send_email_verification_mail(user_pk):
    """ Sending email confirmation for users after registration """
    # TODO NEEDS refactor for activation url
    user = UserAccount.objects.get_or_none(id=user_pk)
    subject, email_from = "Mima email confirmation", settings.EMAIL_HOST_USER
    text_content = "MiMa"
    activate_url = f'{os.environ.get("ACTIVATE_URL", "http://localhost:3000")}/activate/{urlsafe_base64_encode(force_bytes(user_pk))}/{account_activation_token.make_token(user)}/'
    html_content = render_to_string("confirmation_template.html", {
        "username": user.username,
        "activate_url": activate_url
    })

    recipient_list = [user.email, ]
    msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


@shared_task
def send_reset_password_mail(user_pk):
    """ SENDING RESET PASSWORD EMAIL AFTER REQUESTING RESETTING IT """
    user = UserAccount.objects.get_or_none(id=user_pk)
    subject, email_from = "MIMA - Reset Password", settings.EMAIL_HOST_USER
    text_content = "MiMa"
    html_content = f"""
        <h1>Hello {user.username}</h1>
        <p>Click to proceed with resetting the password.</p>
        <a href="{os.environ.get("ACTIVATE_URL", "http://localhost:3000")}/reset_password/{urlsafe_base64_encode(force_bytes(user_pk))}/{account_activation_token.make_token(user)}/">Reset Password</a>
        """
    recipient_list = [user.email, ]
    msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


@shared_task
def send_identity_verification_email(user: UserAccount):
    """ AFTER PROCESSING A PENDING VERIFICATION SEND EMAIL TO USER """

    subject, email_from = "MIMA - VERIFICATION", settings.EMAIL_HOST_USER
    text_content = "MiMa"
    html_content = f"""
        <h1>Hello {user.username}</h1>
        <p>YOUR PROFILE HAS BEEN {user.verification_status}</p>
        """
    recipient_list = [user.email, ]
    msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
