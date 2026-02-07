from python.helpers.extension import Extension
from agent import LoopData
from python.helpers.defer import DeferredTask, THREAD_BACKGROUND

DATA_NAME_TASK = "_organize_history_task"


class OrganizeHistory(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # is there a running task? if yes, skip this round, the wait extension will double check the context size
        task: DeferredTask|None = self.agent.get_data(DATA_NAME_TASK)
        if task and not task.is_ready():
            return

        # start task
        task = DeferredTask(thread_name=THREAD_BACKGROUND)
        task.start_task(self.agent.history.compress)
        # set to agent to be able to wait for it
        self.agent.set_data(DATA_NAME_TASK, task)
