from helpers import socket_handlers


class SchedulerTaskCreate(socket_handlers.JsonApiHandler):
    api_module = "plugins._scheduler.api.scheduler_task_create"
    api_class = "SchedulerTaskCreate"
