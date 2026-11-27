from helpers import socket_handlers


class Message(socket_handlers.JsonApiHandler):
    api_module = "api.message"
    api_class = "Message"
    context_field = "context"
