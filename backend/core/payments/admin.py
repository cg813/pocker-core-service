from django.contrib import admin
from .models import PaymentProvider, PaymentMethod

admin.site.register(PaymentProvider)
admin.site.register(PaymentMethod)
