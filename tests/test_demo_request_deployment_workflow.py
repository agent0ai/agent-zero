from unittest.mock import MagicMock

import pytest

from python.tools.demo_request_create import DemoRequestCreate
from python.tools.demo_request_list import DemoRequestList
from python.tools.devops_deploy import DevOpsDeploy


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.context = MagicMock()
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock(return_value=MagicMock())
    agent.read_prompt = MagicMock(return_value="")
    agent.agent_name = "TestAgent"
    return agent


@pytest.mark.unit
async def test_demo_request_and_deployment_workflow(monkeypatch, tmp_path, mock_agent):
    store_path = tmp_path / "demo_requests.jsonl"
    monkeypatch.setenv("AGENT_JUMBO_DEMO_REQUESTS_PATH", str(store_path))

    create_tool = DemoRequestCreate(
        agent=mock_agent,
        name="demo_request_create",
        method=None,
        args={
            "company": "Acme Construction",
            "email": "ops@acme.example",
            "contact_name": "Alex Admin",
            "environment": "staging",
        },
        message="",
        loop_data=None,
    )
    create_response = await create_tool.execute()
    created = create_response.additional["demo_request"]
    assert created["company"] == "Acme Construction"
    assert created["email"] == "ops@acme.example"
    assert created["id"].startswith("dr_")

    list_tool = DemoRequestList(
        agent=mock_agent,
        name="demo_request_list",
        method=None,
        args={"limit": 10},
        message="",
        loop_data=None,
    )
    list_response = await list_tool.execute()
    rows = list_response.additional["demo_requests"]
    assert len(rows) == 1
    assert rows[0]["id"] == created["id"]
    assert rows[0]["company"] == "Acme Construction"

    deploy_tool = DevOpsDeploy(
        agent=mock_agent,
        name="devops_deploy",
        method=None,
        args={"environment": "staging", "platform": "kubernetes"},
        message="",
        loop_data=None,
    )
    deploy_response = await deploy_tool.execute()
    deployment = deploy_response.additional["deployment"]

    assert deployment["environment"] == "staging"
    assert deployment["platform"] == "kubernetes"
    assert deployment["status"] == "success"
    assert deployment["checks"]["health_checks_passed"] is True
    assert deployment["checks"]["smoke_tests_passed"] is True
    assert deployment["primitives"]["checks"]["status"] == "passed"
    assert deployment["primitives"]["execution"]["status"] == "success"
    assert deployment["primitives"]["record"]["recorded"] is True
    assert deployment["primitives"]["record"]["summary"]["environment"] == "staging"
    assert deployment["primitives"]["record"]["summary"]["platform"] == "kubernetes"
