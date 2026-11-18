from helpers import socket_handlers


class MessageQueueRemove(socket_handlers.JsonApiHandler):
    api_module = "api.message_queue_remove"
    api_class = "MessageQueueRemove"
    context_field = "context"
