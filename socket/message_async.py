from helpers import socket_handlers


class MessageAsync(socket_handlers.JsonApiHandler):
    api_module = "api.message_async"
    api_class = "MessageAsync"
    context_field = "context"
