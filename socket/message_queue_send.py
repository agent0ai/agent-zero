from helpers import socket_handlers


class MessageQueueSend(socket_handlers.JsonApiHandler):
    api_module = "api.message_queue_send"
    api_class = "MessageQueueSend"
    context_field = "context"
