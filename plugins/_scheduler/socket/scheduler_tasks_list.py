from helpers import socket_handlers


class SchedulerTasksList(socket_handlers.JsonApiHandler):
    api_module = "plugins._scheduler.api.scheduler_tasks_list"
    api_class = "SchedulerTasksList"
