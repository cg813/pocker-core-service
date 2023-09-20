from django.urls import path

from .views import TotalReport, MonthlyReport, DailyReport, AdditionalReport, TransactionReport

urlpatterns = [
    path('total_report/', TotalReport.as_view(), name='yearly_report'),
    path('monthly_report/', MonthlyReport.as_view(), name='monthly_report'),
    path('daily_report/', DailyReport.as_view(), name='daily_report'),
    path('additional_report/', AdditionalReport.as_view(), name='additional_report'),
    path('transactions/', TransactionReport.as_view(), name='transactions')
]
