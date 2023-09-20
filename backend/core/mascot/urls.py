from django.urls import path
from modernrpc.views import RPCEntryPoint
from .views import AllTests
urlpatterns = [
    path('rpc/', RPCEntryPoint.as_view()),
    path('all_games/', AllTests.as_view())
]
