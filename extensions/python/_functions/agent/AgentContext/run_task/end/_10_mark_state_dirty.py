from helpers.defer import DeferredTask
from helpers.extension import Extension
from helpers.state_monitor_integration import mark_dirty_all


class MarkStateDirty(Extension):
    def execute(self, data: dict | None = None, **kwargs) -> None:
        task = data.get("result") if isinstance(data, dict) else None
        if isinstance(task, DeferredTask):
            task.add_done_callback(
                lambda _future: mark_dirty_all(
                    reason="agent.AgentContext.run_task_done",
                )
            )
