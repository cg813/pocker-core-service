from collections import defaultdict
from accounts.serializers import WalletSerializer
from modernrpc.core import rpc_method


from .models import (MascotBalanceLog, MascotSessions)
from .serializers import (MascotBalanceLogSerializer, MascotSessionsSerializer)
from .services.game_transactions import (
    MascotTransactionsManager, MascotUserBalanceChange)

from accounts.models import UserAccount, Wallet


@rpc_method
def getBalance(callerId, playerName, currency, gameId="N/A", sessionId=None, sessionAlternativeId="N/A",
               bonusId=None):

    user = UserAccount.objects.get_or_none(id=playerName)
    wallet = Wallet.objects.get(user=user, currency__iso=currency)

    get_game_type = MascotSessions.objects.filter(
        user_id=playerName).first()
    game_type_serialize = MascotSessionsSerializer(get_game_type)

    if game_type_serialize.data['type'] == 'with bonus':
        total_balance = wallet.balance + wallet.bonus_balance
    elif game_type_serialize.data['type'] == 'without bonus':
        total_balance = wallet.balance
    elif game_type_serialize.data['type'] == 'only bonus':
        total_balance = wallet.bonus_balance

    free_round = 0
    if bonusId:
        free_round = wallet.free_spin

    return {
        "balance": int(total_balance * 100),
        "freeroundsLeft": int(free_round)
    }


@rpc_method
def withdrawAndDeposit(callerId, playerName, withdraw, deposit, currency, transactionRef, gameRoundRef="N/A",
                       gameId="N/A", source="N/A", reason="N/A", sessionId="N/A", sessionAlternativeId="N/A",
                       spinDetails="N/A", bonusId=None, chargeFreerounds="N/A"):

    user_balance_change = MascotUserBalanceChange()
    get_game_type = MascotSessions.objects.filter(
        user_id=playerName).first()
    game_type_serialize = MascotSessionsSerializer(get_game_type)

    if deposit > 0:
        dollar_deposit = (deposit / 100)
        user = UserAccount.objects.get_or_none(id=playerName)
        wallet = Wallet.objects.get(user=user, currency__iso=currency)

        if game_type_serialize.data['type'] == 'with bonus':
            initial_balance = wallet.balance + wallet.bonus_balance
        elif game_type_serialize.data['type'] == 'without bonus':
            initial_balance = wallet.balance
        elif game_type_serialize.data['type'] == 'only bonus':
            initial_balance = wallet.bonus_balance

        request_data = dict()

        request_data['user_id'] = playerName
        request_data['game_id'] = gameId
        request_data['game_round'] = gameRoundRef
        request_data['game_transaction_id'] = transactionRef
        request_data['inisial_balance'] = initial_balance
        request_data['amount'] = dollar_deposit
        request_data['final_balance'] = initial_balance + dollar_deposit
        request_data['game_type'] = game_type_serialize.data['type']

        TransactionRecorderDeposit = MascotTransactionsManager(request_data)
        TransactionRecorderDeposit.handle_deposit_request()

        real_amount, bonus_amount = user_balance_change.change_balance(
            'deposit', game_type_serialize.data['type'], dollar_deposit, wallet, playerName)

    if withdraw > 0:
        dollar_withdraw = (withdraw / 100)

        user = UserAccount.objects.get_or_none(id=playerName)
        wallet = Wallet.objects.get(user=user, currency__iso=currency)

        if game_type_serialize.data['type'] == 'with bonus':
            initial_balance = wallet.balance + wallet.bonus_balance
        elif game_type_serialize.data['type'] == 'without bonus':
            initial_balance = wallet.balance
        elif game_type_serialize.data['type'] == 'only bonus':
            initial_balance = wallet.bonus_balance

        request_data = dict()

        request_data['user_id'] = playerName
        request_data['game_id'] = gameId
        request_data['game_round'] = gameRoundRef
        request_data['game_transaction_id'] = transactionRef
        request_data['inisial_balance'] = initial_balance
        request_data['amount'] = dollar_withdraw
        request_data['final_balance'] = initial_balance - dollar_withdraw

        TransactionRecorderWithdraw = MascotTransactionsManager(request_data)
        TransactionRecorderWithdraw.handle_withdraw_request()

        real_amount, bonus_amount = user_balance_change.change_balance(
            'withdraw', game_type_serialize.data['type'], dollar_withdraw, wallet, playerName)

    if withdraw == 0 and deposit == 0:
        user = UserAccount.objects.get_or_none(id=playerName)
        wallet = Wallet.objects.get(user=user, currency__iso=currency)
        if game_type_serialize.data['type'] == 'with bonus':
            initial_balance = wallet.balance + wallet.bonus_balance
        elif game_type_serialize.data['type'] == 'without bonus':
            initial_balance = wallet.balance
        elif game_type_serialize.data['type'] == 'only bonus':
            initial_balance = wallet.bonus_balance
        real_amount = 0
        bonus_amount = 0

    log = MascotBalanceLog.objects.create(
        callerId=callerId,
        playerName=playerName,
        initialBalance=initial_balance,
        finalBalance=wallet.balance,
        withdraw=withdraw,
        deposit=deposit,
        currency=currency,
        transactionRef=transactionRef,
        gameRoundRef=gameRoundRef,
        gameId=gameId,
        source=source,
        reason=reason,
        sessionId=sessionId,
        sessionAlternativeId=sessionAlternativeId,
        spinDetails=spinDetails,
        bonusId=bonusId,
        chargeFreerounds=chargeFreerounds,
        description='withdrawAndDeposit',
        real_amount=real_amount,
        bonus_amount=bonus_amount
    )

    serialize = MascotBalanceLogSerializer(log)
    data = serialize.data

    user = UserAccount.objects.get_or_none(id=playerName)
    wallet = Wallet.objects.get(user=user, currency__iso=currency)

    free_round = 0
    if bonusId:
        free_round = wallet.free_spin - chargeFreerounds
        wallet.free_spin = wallet.free_spin - chargeFreerounds
        wallet.save()

    if game_type_serialize.data['type'] == 'with bonus':
        final_blance = wallet.balance + wallet.bonus_balance
    elif game_type_serialize.data['type'] == 'without bonus':
        final_blance = wallet.balance
    elif game_type_serialize.data['type'] == 'only bonus':
        final_blance = wallet.bonus_balance

    return {
        "newBalance": int(final_blance * 100),
        "transactionId": data['transactionId'],
        "freeroundsLeft": free_round
    }


@rpc_method
def rollbackTransaction(callerId, playerName, transactionRef, gameId="N/A", sessionId="N/A",
                        sessionAlternativeId="N/A"):
    balance_log = MascotBalanceLog.objects.get_or_none(
        transactionRef=transactionRef)
    if balance_log:
        # TODO: HERE WE NEED CHANGES
        balance_log_serialize = MascotBalanceLogSerializer(balance_log)
        balance_log_data = balance_log_serialize.data

        user = UserAccount.objects.get_or_none(id=playerName)
        wallet = Wallet.objects.get(
            user=user, currency__iso=balance_log_data['currency'])
        initial_balance = wallet.balance
        if balance_log_data['deposit'] > 0:
            dollar_deposit_role_back = (balance_log_data['deposit'] / 100)
            wallet.balance -= dollar_deposit_role_back
            wallet.balance = round(wallet.balance, 3)
            wallet.save()
        if balance_log_data['withdraw'] > 0:
            dollar_withdraw_role_back = (balance_log_data['withdraw'] / 100)
            wallet.balance += dollar_withdraw_role_back
            wallet.balance = round(wallet.balance, 3)
            wallet.save()

            MascotBalanceLog.objects.create(
                callerId=balance_log_data['callerId'],
                playerName=balance_log_data['playerName'],
                initialBalance=initial_balance,
                finalBalance=wallet.balance,
                withdraw=balance_log_data['withdraw'],
                deposit=balance_log_data['deposit'],
                currency=balance_log_data['currency'],
                transactionRef=balance_log_data['transactionRef'],
                gameRoundRef=balance_log_data['gameRoundRef'],
                gameId=balance_log_data['gameId'],
                source=balance_log_data['source'],
                reason=balance_log_data['reason'],
                sessionId=balance_log_data['sessionId'],
                sessionAlternativeId=balance_log_data['sessionAlternativeId'],
                spinDetails=balance_log_data['spinDetails'],
                bonusId=balance_log_data['bonusId'],
                chargeFreerounds=balance_log_data['chargeFreerounds'],
                description='withdrawAndDeposit exist - role back done'
            )

    else:
        MascotBalanceLog.objects.create(
            callerId=callerId,
            playerName=playerName,
            initialBalance=0,
            finalBalance=0,
            withdraw=0,
            deposit=0,
            currency='N/A',
            transactionRef=transactionRef,
            gameRoundRef='N/A',
            gameId=gameId,
            source='N/A',
            reason='N/A',
            sessionId=sessionId,
            sessionAlternativeId=sessionAlternativeId,
            spinDetails='N/A',
            bonusId='N/A',
            chargeFreerounds='N/A',
            description='role back'
        )

    return {}
