from types import SimpleNamespace

from agent import AgentContext, UserMessage


def test_nudge_stops_running_context_and_starts_nudge_message():
    context = AgentContext.__new__(AgentContext)
    calls = []

    class _Task:
        def is_alive(self):
            return False

        def kill(self):
            calls.append("kill")

    context.task = _Task()
    context.paused = True
    context.streaming_agent = None
    context.agent0 = SimpleNamespace(
        intervention=None,
        data={},
        read_prompt=lambda _name: "nudge text",
    )

    started = {}

    def fake_run_task(func, *args):
        started["func"] = func
        started["args"] = args
        return "new-task"

    context.run_task = fake_run_task

    result = context.nudge()

    assert calls == ["kill"]
    assert result == "new-task"
    assert started["args"][0] is context.agent0
    assert started["args"][1].system_message == ["nudge text"]
    assert started["args"][1].message == ""


def test_user_message_during_run_sets_intervention():
    context = AgentContext.__new__(AgentContext)

    current = SimpleNamespace(intervention=None, data={})

    context.task = SimpleNamespace(is_alive=lambda: True)
    context.paused = True
    context.streaming_agent = current
    context.agent0 = current

    message = UserMessage("intervene")
    context.communicate(message)

    assert current.intervention is message
    assert context.paused is False
