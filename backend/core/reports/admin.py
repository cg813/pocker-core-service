from django.contrib import admin
from .models import DailyReport
from import_export.admin import ExportActionMixin
from rangefilter.filter import DateRangeFilter


@admin.register(DailyReport)
class UserAccountAdmin(ExportActionMixin, admin.ModelAdmin):
    date_hierarchy = 'report_from'

    read_only_fields_admin = [
        'id', 'is_superuser', 'id_document_1', 'id_document_2', 'last_login', 'registered_at']

    readonly_fields_staff = ['report_from', 'report_to', 'registrations', 'players',
                             'depositors', 'fiat_deposits', 'crypto_deposits', 'total_deposits',
                             'average_deposits', 'real_balance_total', 'bonus_balance_total']

    list_filter = (('report_from', DateRangeFilter), )

    def get_readonly_fields(self, request, obj):
        if request.user.is_superuser:
            return []
        return self.readonly_fields_staff
