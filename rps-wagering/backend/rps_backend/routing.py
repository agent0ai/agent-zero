from django.urls import re_path

from game.consumers import LobbyConsumer

websocket_urlpatterns = [
    re_path(r"ws/lobby/$", LobbyConsumer.as_asgi()),
]
