from django.contrib.auth.tokens import PasswordResetTokenGenerator
from six import text_type


class EmailConfirmationTokenGenerator(PasswordResetTokenGenerator):
    """ Class for getting tokens for email confirmation """

    def _make_hash_value(self, user, timestamp):
        return (
            text_type(user.id) + text_type(timestamp) + text_type(user.is_active)
        )


account_activation_token = EmailConfirmationTokenGenerator()
