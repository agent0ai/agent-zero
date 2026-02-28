import json
import subprocess


FIXTURE_MODULE = "/mnt/wdblack/dev/projects/agent-zero/webui/components/settings/observability/observability-fixture.js"


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
