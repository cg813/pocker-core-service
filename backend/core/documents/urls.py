from django.urls import path

from .views import GetDocumentsView

urlpatterns = [
    path('documents/', GetDocumentsView.as_view())
]
