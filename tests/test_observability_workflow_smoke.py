import types

from python.helpers import master_orchestrator


class DummyContext:
    def __init__(self):
        self.data = {}
        self.id = "test-context"


def test_workflow_run_capture_smoke():
    context = DummyContext()

    run = master_orchestrator.start_run(context, "Smoke Run", metadata={"source": "test"})
    assert run["name"] == "Smoke Run"
    assert run["status"] == "in_progress"

    step_id = master_orchestrator.record_tool_start(
        context,
        tool_name="email",
        trace_id="trace-1",
        agent_name="Agent 0",
        agent_number=0,
        tool_args={"to": "test@example.com"},
        auto_store=True,
    )
    assert step_id is not None

    master_orchestrator.record_tool_end(
        context,
        step_id=step_id,
        status="success",
        duration_ms=123.4,
    )

    saved = master_orchestrator.save_active_run(context, label="Snapshot")
    assert saved is not None
    assert saved["label"] == "Snapshot"
    assert len(saved["steps"]) == 1

    cleared = master_orchestrator.clear_store(context)
    assert cleared["runs"] == []
    assert cleared["saved_runs"] == []
