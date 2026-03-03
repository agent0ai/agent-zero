import pytest

from agent import Agent, AgentContext, UserMessage
from initialize import initialize_agent


@pytest.mark.asyncio
async def test_e2e_happy_intent_parses_and_routes_to_review(monkeypatch):
    from python.helpers.tool import Response
    from python.tools import call_subordinate

    called = {}

    async def fake_execute(self, message="", reset="", **kwargs):
        called["kwargs"] = kwargs
        return Response(message="ok-review", break_loop=False)

    monkeypatch.setattr(call_subordinate.Delegation, "execute", fake_execute, raising=True)

    config = initialize_agent(override_settings={"agent_profile": "gatekeeper"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: review\n"
                    "jurisdiction: NY, USA\n"
                    "review_focus: risks + redlines\n"
                    "```text\n"
                    "This Agreement is made between Party A and Party B...\n"
                    "...\n"
                    "Termination: either party may terminate at any time.\n"
                    "```\n"
                ),
                attachments=[],
            )
        )
        result = await agent.monologue()
        assert "profile: legalflow_review" in result
        assert "ok-review" in result
        assert called["kwargs"]["profile"] == "legalflow_review"
        assert called["kwargs"]["slot"] == "review"
    finally:
        AgentContext.remove(agent.context.id)


@pytest.mark.asyncio
async def test_e2e_negative_missing_intent_triggers_structured_questions(monkeypatch):
    from python.tools import call_subordinate

    async def should_not_run(*args, **kwargs):
        raise AssertionError("Subagent should not be called when intake is incomplete")

    monkeypatch.setattr(call_subordinate.Delegation, "execute", should_not_run, raising=True)

    config = initialize_agent(override_settings={"agent_profile": "gatekeeper"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(message="I need help with a legal matter.", attachments=[])
        )
        result = await agent.monologue()
        assert "intake needed" in result
        assert "intent (choose one)" in result
    finally:
        AgentContext.remove(agent.context.id)


@pytest.mark.asyncio
async def test_e2e_negative_missing_jurisdiction_triggers_structured_questions(monkeypatch):
    from python.tools import call_subordinate

    async def should_not_run(*args, **kwargs):
        raise AssertionError("Subagent should not be called when intake is incomplete")

    monkeypatch.setattr(call_subordinate.Delegation, "execute", should_not_run, raising=True)

    config = initialize_agent(override_settings={"agent_profile": "gatekeeper"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(message="Draft a simple NDA for two startups.", attachments=[])
        )
        result = await agent.monologue()
        assert "intake needed" in result
        assert "jurisdiction" in result
    finally:
        AgentContext.remove(agent.context.id)


@pytest.mark.asyncio
async def test_e2e_negative_docs_missing_format_triggers_structured_questions(monkeypatch):
    from python.tools import call_subordinate

    async def should_not_run(*args, **kwargs):
        raise AssertionError("Subagent should not be called when intake is incomplete")

    monkeypatch.setattr(call_subordinate.Delegation, "execute", should_not_run, raising=True)

    config = initialize_agent(override_settings={"agent_profile": "gatekeeper"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: docs\n"
                    "jurisdiction: CA, USA\n"
                    "topic: intake checklist\n"
                    "audience: paralegals\n"
                ),
                attachments=[],
            )
        )
        result = await agent.monologue()
        assert "intake needed" in result
        assert "format" in result
    finally:
        AgentContext.remove(agent.context.id)

