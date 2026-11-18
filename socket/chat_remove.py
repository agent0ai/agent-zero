from helpers import socket_handlers


class RemoveChat(socket_handlers.JsonApiHandler):
    api_module = "api.chat_remove"
    api_class = "RemoveChat"
    context_field = "context"
