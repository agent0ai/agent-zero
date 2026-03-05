from django.urls import path

from .views import HealthView, LobbyMatchView, LobbyRoomListView, OneInchQuoteView, YieldEstimateView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("lobby/match/", LobbyMatchView.as_view(), name="lobby-match"),
    path("lobby/rooms/", LobbyRoomListView.as_view(), name="lobby-rooms"),
    path("swap/quote/", OneInchQuoteView.as_view(), name="swap-quote"),
    path("yield/estimate/", YieldEstimateView.as_view(), name="yield-estimate"),
]
