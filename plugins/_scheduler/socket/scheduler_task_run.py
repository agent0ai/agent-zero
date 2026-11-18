from helpers import socket_handlers


class SchedulerTaskRun(socket_handlers.JsonApiHandler):
    api_module = "plugins._scheduler.api.scheduler_task_run"
    api_class = "SchedulerTaskRun"
