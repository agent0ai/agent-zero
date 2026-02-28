import threading
from unittest.mock import patch

import pytest

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
        output={
            "deployment": {
                "environment": "staging",
                "status": "success",
                "telemetry": {"failed_stage": None, "stages": [{"name": "checks", "status": "passed"}]},
            }
        },
    )

    saved = master_orchestrator.save_active_run(context, label="Snapshot")
    assert saved is not None
    assert saved["label"] == "Snapshot"
    assert len(saved["steps"]) == 1
    step = saved["steps"][0]
    assert step["deployment_environment"] == "staging"
    assert step["deployment_status"] == "success"
    assert step["deployment_telemetry"]["failed_stage"] is None
    assert "output" in step

    cleared = master_orchestrator.clear_store(context)
    assert cleared["runs"] == []
    assert cleared["saved_runs"] == []


def test_workflow_output_redacts_sensitive_and_truncates_large_payload():
    context = DummyContext()
    master_orchestrator.start_run(context, "Redaction Run")

    step_id = master_orchestrator.record_tool_start(
        context,
        tool_name="devops_deploy",
        trace_id="trace-redact",
        agent_name="Agent 0",
        agent_number=0,
        tool_args={},
        auto_store=True,
    )
    assert step_id is not None

    huge_blob = "x" * 20000
    master_orchestrator.record_tool_end(
        context,
        step_id=step_id,
        status="success",
        duration_ms=10.0,
        output={
            "api_key": "super-secret-key",
            "nested": {"password": "hunter2"},
            "blob": huge_blob,
            "deployment": {
                "environment": "staging",
                "status": "success",
                "platform": "kubernetes",
                "telemetry": {
                    "failed_stage": None,
                    "stages": [{"name": "checks", "status": "passed", "duration_ms": 4}],
                },
            },
        },
    )

    saved = master_orchestrator.save_active_run(context, label="Redaction Snapshot")
    assert saved is not None
    step = saved["steps"][0]
    assert step["output_truncated"] is True
    assert step["output"]["deployment"]["environment"] == "staging"
    assert step["output"]["_truncated"]["reason"] == "size_limit"
    assert step["output"]["_truncated"]["original_chars"] > step["output"]["_truncated"]["max_chars"]
    assert step["output"].get("api_key") is None


class _DummyRequest:
    pass


@pytest.mark.asyncio
async def test_workflow_get_contract_includes_deployment_telemetry():
    from python.api.workflow_get import WorkflowGet

    context = DummyContext()
    run = master_orchestrator.start_run(context, "Contract Run")
    step_id = master_orchestrator.record_tool_start(
        context,
        tool_name="devops_deploy",
        trace_id="trace-contract",
        agent_name="Agent 0",
        agent_number=0,
        tool_args={"environment": "staging"},
        auto_store=True,
    )
    assert step_id is not None

    master_orchestrator.record_tool_end(
        context,
        step_id=step_id,
        status="success",
        duration_ms=50.0,
        output={
            "deployment": {
                "environment": "staging",
                "status": "success",
                "telemetry": {
                    "failed_stage": None,
                    "stages": [
                        {"name": "checks", "status": "passed", "duration_ms": 5},
                        {"name": "execute", "status": "passed", "duration_ms": 12},
                        {"name": "record", "status": "passed", "duration_ms": 3},
                    ],
                },
            }
        },
    )
    assert run["run_id"]

    handler = WorkflowGet(app=None, thread_lock=threading.Lock())
    with patch.object(handler, "use_context", return_value=context):
        result = await handler.process({"context": "test-context"}, _DummyRequest())

    assert "runs" in result
    assert result["active_run_id"] == run["run_id"]
    step = result["runs"][0]["steps"][0]
    assert step["deployment_environment"] == "staging"
    assert step["deployment_status"] == "success"
    assert step["deployment_telemetry"]["failed_stage"] is None
    assert len(step["deployment_telemetry"]["stages"]) == 3
