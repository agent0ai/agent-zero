import pytest

from agent import Agent, UserMessage, AgentContext
from initialize import initialize_agent


def test_legalflow_profiles_are_available():
    from python.helpers import subagents

    agents = subagents.get_agents_dict()
    for key in (
        "gatekeeper",
        "legalflow_research",
        "legalflow_draft",
        "legalflow_review",
        "legalflow_docs",
    ):
        assert key in agents, f"Expected agent profile '{key}' to exist"


@pytest.mark.asyncio
async def test_gatekeeper_missing_intake_fields_short_circuits_with_questions():
    config = initialize_agent(override_settings={"agent_profile": "gatekeeper"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(message="Please draft a demand letter.", attachments=[])
        )
        result = await agent.monologue()
        assert "LegalFlow Gatekeeper" in result
        assert "intake needed" in result
        assert "jurisdiction" in result
        assert "facts" in result
    finally:
        AgentContext.remove(agent.context.id)


@pytest.mark.asyncio
async def test_gatekeeper_routes_to_correct_profile_when_intake_complete(monkeypatch):
    from python.helpers.tool import Response
    from python.tools import call_subordinate

    calls = {}

    async def fake_execute(self, message="", reset="", **kwargs):
        calls["message"] = message
        calls["reset"] = reset
        calls["kwargs"] = kwargs
        return Response(message="routed-ok", break_loop=False)

    monkeypatch.setattr(call_subordinate.Delegation, "execute", fake_execute, raising=True)

    config = initialize_agent(override_settings={"agent_profile": "gatekeeper"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: research\n"
                    "jurisdiction: CA, USA\n"
                    "question: What is the statute of limitations for breach of contract?\n"
                ),
                attachments=[],
            )
        )
        result = await agent.monologue()
        assert "(Intent: research" in result
        assert "profile: legalflow_research" in result
        assert "routed-ok" in result

        assert calls["reset"] == "true"
        assert calls["kwargs"]["profile"] == "legalflow_research"
        assert calls["kwargs"]["slot"] == "research"
        assert "LEGALFLOW INTAKE" in calls["message"]
        assert "question:" in calls["message"]
    finally:
        AgentContext.remove(agent.context.id)

