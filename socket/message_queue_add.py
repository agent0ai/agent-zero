from helpers import socket_handlers


class MessageQueueAdd(socket_handlers.JsonApiHandler):
    api_module = "api.message_queue_add"
    api_class = "MessageQueueAdd"
    context_field = "context"
