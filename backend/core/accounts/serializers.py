from uuid import uuid4
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import (UserAccount, Currency, Transaction, Wallet)
from accounts.services.utils import upload_to_bucket, get_bucket


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    captcha_token = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError('Password must match')
        return data

    def save(self):
        data = {
            key: value for key, value in self.validated_data.items()
            if key not in ('password', 'confirm_password')
        }
        data['password'] = self.validated_data['password']
        return self.Meta.model.objects.create_user(**data)

    class Meta:
        model = UserAccount
        fields = (
            'id', 'username', 'password', 'confirm_password', 'captcha_token', 'email', 'birth_date'
        )
        read_only_fields = ('id', )


class LogInSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        user.logged_out = False
        user.save()

        token = super().get_token(user)
        user_data = UserSerializer(user).data
        for key, value in user_data.items():
            if key != 'id':
                token[key] = value
        return token


class UserDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAccount
        fields = ('first_name', 'last_name', 'id', 'verification_status', 'username')


class UserActivationSerializer(serializers.Serializer):
    uid64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    uid64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAccount
        fields = ('first_name', 'last_name', 'email', 'country', 'city', 'zip', 'address',
                  'phone_number', 'is_pep', 'birth_date', 'gender', 'identification_number',
                  'identification_document_1', 'identification_document_2')


class UserProfileVerificationSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    zip = serializers.CharField(required=True)
    birth_date = serializers.DateField(required=True)
    gender = serializers.ChoiceField(['male', 'female', 'other'])
    address = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    is_pep = serializers.BooleanField(required=True)
    identification_number = serializers.CharField(required=True)
    identification_document_1 = serializers.ImageField(required=True)
    identification_document_2 = serializers.ImageField()

    def upload_image_to_bucket(self, bucket, file):
        filename = f'{uuid4()}.png'
        upload_to_bucket(file, bucket, filename)
        print(filename)
        return filename

    def save(self, user: UserAccount):
        bucket = get_bucket()

        user.first_name = self.validated_data.get('first_name')
        user.last_name = self.validated_data.get('last_name')
        user.country = self.validated_data.get('country')
        user.city = self.validated_data.get('city')
        user.zip = self.validated_data.get('zip')
        user.address = self.validated_data.get('address')
        user.phone_number = self.validated_data.get('phone_number')
        user.is_pep = self.validated_data.get('is_pep')
        user.identification_number = self.validated_data.get('identification_number')
        user.identification_document_1 = self.upload_image_to_bucket(bucket, self.validated_data.get('identification_document_1'))

        if file := self.validated_data.get('identification_document_2'):
            user.identification_document_2 = self.upload_image_to_bucket(bucket, file)

        user.verification_status = 'pending'
        user.save()


class CurrencySerializer(serializers.ModelSerializer):

    class Meta:
        model = Currency
        fields = ('id', 'symbol', 'iso', 'full_name',
                  'is_crypto', 'divider', 'parent_currency', 'is_main')


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = ('id', 'transaction_id', 'user', 'initial_amount', 'amount',
                  'currency', 'transaction_start_date', 'transaction_end_date',
                  'transaction_type', 'transaction_status',
                  'transaction_oder_number', 'game', 'game_round_id',
                  'game_transaction_id', 'description',
                  'balance', 'payment_provider', 'created_at')


class WalletSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wallet
        fields = ('id', 'user', 'currency', 'balance', 'active')
