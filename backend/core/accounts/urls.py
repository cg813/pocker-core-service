from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import routers
from .views import (
    SignUpView,
    LogInView,
    GetUserDataView,
    ActivateUserAccount,
    CurrencyViewSet,
    WalletViewSet,
    ResetPassword,
    ProfileVerificationView,
    LogOutView
)

router = routers.SimpleRouter()
router.register('currency', CurrencyViewSet)
router.register('wallet', WalletViewSet)

urlpatterns = [
    path('sign_up/', SignUpView.as_view(), name='sign_up'),
    path('log_in/', LogInView.as_view(), name='log_in'),
    path('log_out/', LogOutView.as_view(), name='log_out'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user_data/', GetUserDataView.as_view(), name='user_data'),
    path('activate/user/', ActivateUserAccount.as_view(), name="user_activation"),
    path('reset_password/', ResetPassword.as_view(), name='reset_password'),
    path('profile/', ProfileVerificationView.as_view(), name='profile'),
    path('', include(router.urls)),
]
