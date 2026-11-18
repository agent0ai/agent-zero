from helpers import socket_handlers


class SchedulerTaskDelete(socket_handlers.JsonApiHandler):
    api_module = "plugins._scheduler.api.scheduler_task_delete"
    api_class = "SchedulerTaskDelete"
