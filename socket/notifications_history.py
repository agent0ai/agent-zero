from helpers import socket_handlers


class NotificationsHistory(socket_handlers.JsonApiHandler):
    api_module = "api.notifications_history"
    api_class = "NotificationsHistory"
