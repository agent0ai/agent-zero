from helpers import socket_handlers


class NotificationCreate(socket_handlers.JsonApiHandler):
    api_module = "api.notification_create"
    api_class = "NotificationCreate"
