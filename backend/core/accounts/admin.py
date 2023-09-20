import os

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from import_export.admin import ExportActionMixin
from django.utils.html import format_html
from rangefilter.filter import DateRangeFilter

from .models import (
    UserAccount, Currency, Rate, Wallet, Transaction)


class UserAdmin(DefaultUserAdmin):
    pass


# admin.site.register(UserAccount)
admin.site.register(Currency)
admin.site.register(Rate)


@admin.register(UserAccount)
class UserAccountAdmin(ExportActionMixin, admin.ModelAdmin):
    date_hierarchy = 'registered_at'

    def id_document_1(self, obj):
        return format_html('<img src="https://storage.googleapis.com/static.mima-poker.cc/{}/{}" width="auto" height="200px" />'.format(
            os.environ.get('BUCKET_FOLDER_NAME'), obj.identification_document_1))

    def id_document_2(self, obj):
        return format_html('<img src="https://storage.googleapis.com/static.mima-poker.cc/{}/{}" width="auto" height="200px" />'.format(
            os.environ.get('BUCKET_FOLDER_NAME'), obj.identification_document_2))

    def id(self, obj):
        return obj.id

    search_fields = ('username', 'email')

    list_filter = (('registered_at', DateRangeFilter),
                   'verification_status', 'groups')

    fields = ('id', 'username', 'first_name', 'last_name', 'email', 'birth_date', 'gender',
              'identification_number', 'country', 'city', 'zip', 'address', 'phone_number',
              'registered_at', 'is_pep', 'is_admin', 'is_staff', 'is_superuser',
              'id_document_1', 'id_document_2', 'last_login', 'verification_status',
              'is_active', 'is_dealer', 'BTC_TO_USD', 'ETH_TO_USD', 'groups', 'logged_out')

    read_only_fields_admin = [
        'id', 'is_superuser', 'id_document_1', 'id_document_2', 'last_login', 'registered_at']

    readonly_fields_staff = ['id', 'is_admin', 'is_staff', 'is_superuser', 'gender',
                             'id_document_1', 'id_document_2', 'last_login', 'groups', 'BTC_TO_USD',
                             'registered_at', 'ETH_TO_USD']

    def get_readonly_fields(self, request, obj):
        if request.user.is_superuser:
            return ['id', 'id_document_1', 'id_document_2']
        if request.user.is_admin:
            return self.read_only_fields_admin
        return self.readonly_fields_staff


@admin.register(Transaction)
class TransactionAdmin(ExportActionMixin, admin.ModelAdmin):
    date_hierarchy = 'transaction_start_date'
    search_fields = ('transaction_order_number', 'user__username', 'game_round',
                     'user__email', 'game__name', 'amount')
    list_filter = (('transaction_start_date', DateRangeFilter),
                   'transaction_type', 'transaction_status')

    read_only_fields = ['transaction_id', 'user', 'initial_amount', 'amount', 'currency',
                        'rate', 'fee', 'transaction_start_date', 'transaction_end_date',
                        'transaction_type', 'transaction_order_number', 'game', 'game_round',
                        'game_transaction_id', 'balance', 'payment_provider']

    def get_readonly_fields(self, request, obj):
        if request.user.is_superuser:
            return []
        return self.read_only_fields


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__email')
