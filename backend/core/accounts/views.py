from rest_framework.views import APIView
from rest_framework import status, permissions, viewsets, mixins
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated

from .models import (
    Currency,
    # Transaction,
    UserAccount,
    Wallet
)

from .serializers import (
    UserProfileSerializer,
    UserProfileVerificationSerializer,
    UserSerializer,
    LogInSerializer,
    UserDataSerializer,
    UserActivationSerializer,
    ResetPasswordSerializer,
    CurrencySerializer,
    WalletSerializer,
)
from .services.auth_actions import activate_user, reset_password
from .tasks import send_email_verification_mail, send_reset_password_mail
from .services.utils import validate_captcha_token, get_or_update_notify_bonus


class SignUpView(APIView):
    permission_classes = (permissions.AllowAny, )
    authentication_classes = ()

    @staticmethod
    def post(request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            validate_captcha_token(request.data.get('captcha_token'))
            user = serializer.save()
            send_email_verification_mail.delay(user.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogInView(TokenObtainPairView):
    serializer_class = LogInSerializer


class LogOutView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        user = request.user
        user.logged_out = True
        user.save()

        return Response(status=status.HTTP_200_OK)


class GetUserDataView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        serializer = UserDataSerializer(request.user)
        data = serializer.data

        user = UserAccount.objects.get_or_none(pk=request.user.id)

        wallet = Wallet.objects.get(user=user, active=True)
        data['deposit'] = round(wallet.balance, 2)
        data['bonus_balance'] = wallet.bonus_balance
        data['display_bonus_notification'] = get_or_update_notify_bonus(wallet)

        # CHECK IF USER PROFILE IS PAYMENT VERIFIED
        data['payment_verified'] = True
        for each in ['first_name', 'last_name', 'email', 'phone_number',
                     'country', 'city', 'address', 'zip']:
            if getattr(user, each) is None:
                data['payment_verified'] = False

        return Response(data, status=status.HTTP_200_OK)


class ActivateUserAccount(APIView):
    permission_classes = (permissions.AllowAny, )
    authentication_classes = ()

    @staticmethod
    def post(request):
        serializer = UserActivationSerializer(data=request.data)
        if serializer.is_valid():
            if activate_user(serializer.data.get("uid64"), serializer.data.get(
                'token'
            )):
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ResetPassword(APIView):

    permission_classes = (permissions.AllowAny, )
    authentication_classes = ()

    @staticmethod
    def get(request):
        email = request.query_params.get('email')

        user = UserAccount.objects.get_or_none(email=email)

        if user:
            if user.is_active:
                send_reset_password_mail.delay(user.id)

                return Response(
                    data={
                        'message': 'mail was sent!'
                    },
                    status=status.HTTP_200_OK
                )
            return Response(
                data={
                    'message': 'accounts is not activated'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            data={
                'message': 'User does not exist'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    @staticmethod
    def post(request):
        serializer = ResetPasswordSerializer(request.data)
        if serializer.is_valid:
            if serializer.data.get('password') == serializer.data.get('confirm_password'):
                if reset_password(serializer.data.get("uid64"), serializer.data.get('token'),
                                  serializer.data.get('password')):
                    return Response(status=status.HTTP_200_OK)

                return Response(
                    data={
                        'message': 'token is not valid'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                data={
                    'message': 'passwords do not match'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CurrencyViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.CreateModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer


class WalletViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer


class ProfileVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        print('ASJFHLAKSJHFLKASFJH')
        print(request.user)
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def post(request):
        if request.user.verification_status == 'unverified':
            serializer = UserProfileVerificationSerializer(request.user, data=request.data)
            if serializer.is_valid():
                serializer.save(request.user)
                return Response(serializer.data)

            return Response(data={
                'message': 'invalid data'
            }, status=status.HTTP_400_BAD_REQUEST)

        messages = {
            'pending': 'verification is pending',
            'verified': 'profile is already verified',
            'rejected': 'your profile is rejected'
        }

        return Response(data={
            'message': messages[request.user.verification_status]
        }, status=status.HTTP_400_BAD_REQUEST)
