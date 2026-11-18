from helpers import socket_handlers


class SchedulerTaskUpdate(socket_handlers.JsonApiHandler):
    api_module = "plugins._scheduler.api.scheduler_task_update"
    api_class = "SchedulerTaskUpdate"
