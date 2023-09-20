from django.urls import path
from .views import (AlphaPoCallback, AlphapoDepositExchangeAddressView, AlphapoPaymentSpecificationView,
                    DepositView, DixonPayCallback, DixonPayDepositView,
                    IBANWithdrawalView, PaymentProviderView, UserWithdrawalView,
                    WithdrawalView, WonderlandPayCallback,
                    PaymentMethodView, InterkassaCallback, AlphapoWithdrawalExchangeView, EnsopayCallback,
                    OdeonpayCallback, TransactionHistory, OdeonpayWithdrawalView, InterkassaWithdrawalCallback,
                    SyspayCallback, NeobanqCallback, PayecardsCallback, SyspayPaymentSuccess, SyspayPaymentFail,
                    FintechCashierDepositCallback, CertusCallback)

urlpatterns = [
    path('deposit/', DepositView.as_view(), name='deposit'),
    path('deposit/dixonpay/', DixonPayDepositView.as_view(), name='deposit_dixonpay'),

    path('withdrawal/', WithdrawalView.as_view(), name='withdrawal'),

    path('withdrawal/iban/', IBANWithdrawalView.as_view(), name='iban_withdrawal'),
    path('withdrawals/', UserWithdrawalView.as_view(), name='user_withdrawal'),

    path('wonderlandpay/callback/', WonderlandPayCallback.as_view(), name='wonderlandpay_callback'),
    path('dixonpay/callback/', DixonPayCallback.as_view(), name='dixonpay_callback'),
    path('interkassa/callback/', InterkassaCallback.as_view(), name='interkassa_callback'),

    path('interkassa/withdrawal_callback/', InterkassaWithdrawalCallback.as_view(), name='interkassa_withdrawal_callback'),

    path('alphapo/specifications/', AlphapoPaymentSpecificationView.as_view(), name='alphapo_specification'),
    path('alphapo/withdrawal_exchange/', AlphapoWithdrawalExchangeView.as_view(), name='alphapo_withdrawal_exchange'),
    path('alphapo/callback/', AlphaPoCallback.as_view(), name='alphapo_callback'),

    path('ensopay/callback/', EnsopayCallback.as_view(), name='ensopay_callback'),

    path('odeonpay/callback/', OdeonpayCallback.as_view(), name='odeonpay_callback'),
    path('odeonpay/withdrawal/', OdeonpayWithdrawalView.as_view(), name='odeonpay_withdrawal_callback'),

    path('syspay/callback/', SyspayCallback.as_view(), name='syspay_callback'),

    path('payecards/callback/', PayecardsCallback.as_view(), name='payecards_callback'),

    path('neobanq/callback/', NeobanqCallback.as_view(), name='neobanq_callback'),

    # for syspay redirect
    path('syspay/payment-success/', SyspayPaymentSuccess.as_view(), name='neobanq_callback'),
    path('syspay/payment-failed/', SyspayPaymentFail.as_view(), name='neobanq_callback'),

    path('fintech_cashier/callback/', FintechCashierDepositCallback.as_view(), name='fintech_cashier_callback'),

    path('certus/callback/', CertusCallback.as_view(), name='certus_callback'),

    path('methods/', PaymentMethodView.as_view(), name='method'),
    path('providers/', PaymentProviderView.as_view(), name='providers'),
    path('alphapo/address/', AlphapoDepositExchangeAddressView.as_view(), name='alphapo_address'),


    path('transaction/history/', TransactionHistory.as_view(), name='user_transaction_history'),
]
