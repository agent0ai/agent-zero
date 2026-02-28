import json
import subprocess
from pathlib import Path


FIXTURE_MODULE = "/mnt/wdblack/dev/projects/agent-zero/webui/components/settings/observability/observability-fixture.js"
OBSERVABILITY_HTML = Path("/mnt/wdblack/dev/projects/agent-zero/webui/components/settings/observability/observability.html")
OBSERVABILITY_STORE = Path(
    "/mnt/wdblack/dev/projects/agent-zero/webui/components/settings/observability/observability-store.js"
)


def _run_node_eval(script: str) -> str:
    result = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_read_observability_fixture_normalizes_payload():
    script = f"""
const m = await import('file://{FIXTURE_MODULE}');
const payload = m.readObservabilityFixture({{
  __OBSERVABILITY_TEST_DATA__: {{
    events: [{{ tool_name: 'devops_deploy' }}],
    stats: {{ devops_deploy: {{ count: 1 }} }},
    workflowRuns: [{{ run_id: 'run_1' }}],
    savedRuns: [{{ run_id: 'run_1', saved_at: '2026-02-28T00:00:00Z' }}],
    activeRunId: 'run_1',
  }}
}});
console.log(JSON.stringify(payload));
"""
    out = _run_node_eval(script)
    data = json.loads(out)

    assert data["events"][0]["tool_name"] == "devops_deploy"
    assert data["stats"]["devops_deploy"]["count"] == 1
    assert data["runs"][0]["run_id"] == "run_1"
    assert data["saved_runs"][0]["run_id"] == "run_1"
    assert data["active_run_id"] == "run_1"


def test_read_observability_fixture_returns_null_without_fixture():
    script = f"""
const m = await import('file://{FIXTURE_MODULE}');
const payload = m.readObservabilityFixture({{}});
console.log(payload === null ? 'null' : 'not-null');
"""
    out = _run_node_eval(script)
    assert out == "null"


def test_read_observability_fixture_preserves_deployment_stages_shape():
    script = f"""
const m = await import('file://{FIXTURE_MODULE}');
const payload = m.readObservabilityFixture({{
  __OBSERVABILITY_TEST_DATA__: {{
    workflowRuns: [{{
      run_id: 'run_deploy',
      steps: [{{
        step_id: 'step_1',
        deployment_telemetry: {{
          failed_stage: null,
          stages: [
            {{ name: 'checks', status: 'passed', duration_ms: 3 }},
            {{ name: 'execute', status: 'passed', duration_ms: 7 }}
          ]
        }}
      }}]
    }}]
  }}
}});
console.log(JSON.stringify(payload.runs[0].steps[0].deployment_telemetry));
"""
    out = _run_node_eval(script)
    telemetry = json.loads(out)
    assert telemetry["failed_stage"] is None
    assert len(telemetry["stages"]) == 2
    assert telemetry["stages"][0]["name"] == "checks"
    assert telemetry["stages"][1]["duration_ms"] == 7


def test_observability_markup_contains_fixture_and_badge_bindings():
    html = OBSERVABILITY_HTML.read_text(encoding="utf-8")
    store = OBSERVABILITY_STORE.read_text(encoding="utf-8")

    assert "readObservabilityFixture(window)" in store
    assert "statusClass(status)" in store
    assert ':class="$store.observabilityStore.statusClass(step.status)"' in html
    assert ':class="$store.observabilityStore.statusClass(stage.status)"' in html
    assert "workflow-deployment-stages" in html
