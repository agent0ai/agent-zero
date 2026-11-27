from helpers import socket_handlers


class NotificationsMarkRead(socket_handlers.JsonApiHandler):
    api_module = "api.notifications_mark_read"
    api_class = "NotificationsMarkRead"
