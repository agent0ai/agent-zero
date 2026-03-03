import threading

import pytest
from flask import Flask, request

from agent import Agent, AgentContext, UserMessage
from initialize import initialize_agent


@pytest.mark.asyncio
async def test_e2e_export_blocked_until_review_passes(monkeypatch):
    from python.api.chat_export import ExportChat
    from python.helpers import persist_chat
    from python.helpers.review_gate import LEGALFLOW_REVIEW_GATE_KEY
    from python.helpers.tool import Response
    from python.tools import call_subordinate

    async def fake_execute(self, message="", reset="", **kwargs):
        profile = kwargs.get("profile")
        if profile == "legalflow_draft":
            return Response(message="DRAFT OUTPUT", break_loop=False)
        if profile == "legalflow_review":
            return Response(message="REVIEW OUTPUT", break_loop=False)
        return Response(message="ok", break_loop=False)

    monkeypatch.setattr(call_subordinate.Delegation, "execute", fake_execute, raising=True)

    config = initialize_agent(override_settings={"agent_profile": "gatekeeper"})
    agent = Agent(0, config)
    try:
        # Draft -> review required
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: draft\n"
                    "jurisdiction: CA, USA\n"
                    "document_type: petição inicial\n"
                    "facts: Customer failed to pay two invoices totaling $12,500.\n"
                ),
                attachments=[],
            )
        )
        draft_result = await agent.monologue()
        assert "DRAFT OUTPUT" in draft_result
        assert "## Disclaimer" in draft_result

        gate = agent.context.get_output_data(LEGALFLOW_REVIEW_GATE_KEY)
        assert gate["status"] == "required"

        # Export blocked before passing review
        app = Flask("test_export_gate")
        handler = ExportChat(app, threading.RLock())
        with app.test_request_context(
            "/chat_export", method="POST", json={"ctxid": agent.context.id}
        ):
            blocked = await handler.process({"ctxid": agent.context.id}, request)
            assert hasattr(blocked, "status_code")
            assert blocked.status_code == 409

        # Review -> passing status stored
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: review\n"
                    "jurisdiction: CA, USA\n"
                    "review_focus: risks + redlines\n"
                    "```text\n"
                    "This Agreement is made between Party A and Party B.\n"
                    "Termination: either party may terminate with 30 days notice.\n"
                    "## Fontes\n"
                    "[1] Tipo: Oficial (Planalto)\n"
                    "Identificador: urn:lex:br:federal:lei:1990-09-11;8078\n"
                    "Data: 1990-09-11\n"
                    "URL: https://www.planalto.gov.br/ccivil_03/leis/l8078.htm\n"
                    "Trecho: \"Texto\"\n"
                    "```\n"
                ),
                attachments=[],
            )
        )
        review_result = await agent.monologue()
        assert "Review status:" in review_result
        assert "Checklist:" in review_result
        assert "Risk flags:" in review_result
        assert "Citation validation" in review_result
        assert "## Disclaimer" in review_result

        gate2 = agent.context.get_output_data(LEGALFLOW_REVIEW_GATE_KEY)
        assert gate2["status"] == "passed"

        # Export allowed after passing review
        monkeypatch.setattr(
            persist_chat, "export_json_chat", lambda ctx: '{"ok": true}', raising=True
        )
        with app.test_request_context(
            "/chat_export", method="POST", json={"ctxid": agent.context.id}
        ):
            ok = await handler.process({"ctxid": agent.context.id}, request)
            assert isinstance(ok, dict)
            assert ok["content"] == '{"ok": true}'
    finally:
        AgentContext.remove(agent.context.id)


@pytest.mark.asyncio
async def test_e2e_failed_review_then_corrected_review_unblocks_export(monkeypatch):
    from python.api.chat_export import ExportChat
    from python.helpers import persist_chat
    from python.helpers.review_gate import LEGALFLOW_REVIEW_GATE_KEY
    from python.helpers.tool import Response
    from python.tools import call_subordinate

    async def fake_execute(self, message="", reset="", **kwargs):
        profile = kwargs.get("profile")
        if profile == "legalflow_draft":
            return Response(message="DRAFT OUTPUT", break_loop=False)
        if profile == "legalflow_review":
            return Response(message="REVIEW OUTPUT", break_loop=False)
        return Response(message="ok", break_loop=False)

    monkeypatch.setattr(call_subordinate.Delegation, "execute", fake_execute, raising=True)

    config = initialize_agent(override_settings={"agent_profile": "gatekeeper"})
    agent = Agent(0, config)
    try:
        # Draft -> review required
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: draft\n"
                    "jurisdiction: CA, USA\n"
                    "document_type: petição inicial\n"
                    "facts: Customer failed to pay two invoices totaling $12,500.\n"
                ),
                attachments=[],
            )
        )
        await agent.monologue()

        gate = agent.context.get_output_data(LEGALFLOW_REVIEW_GATE_KEY)
        assert gate["status"] == "required"

        # Review (fail) -> export still blocked
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: review\n"
                    "jurisdiction: CA, USA\n"
                    "review_focus: risks + redlines\n"
                    "```text\n"
                    "This Agreement is made between Party A and Party B.\n"
                    "TODO: add governing law clause.\n"
                    "Termination: either party may terminate with 30 days notice.\n"
                    "```\n"
                ),
                attachments=[],
            )
        )
        await agent.monologue()

        gate_failed = agent.context.get_output_data(LEGALFLOW_REVIEW_GATE_KEY)
        assert gate_failed["status"] == "failed"

        app = Flask("test_export_gate_failed_then_corrected")
        handler = ExportChat(app, threading.RLock())
        with app.test_request_context(
            "/chat_export", method="POST", json={"ctxid": agent.context.id}
        ):
            blocked = await handler.process({"ctxid": agent.context.id}, request)
            assert hasattr(blocked, "status_code")
            assert blocked.status_code == 409

        # Corrected review (pass) -> export allowed
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: review\n"
                    "jurisdiction: CA, USA\n"
                    "review_focus: risks + redlines\n"
                    "```text\n"
                    "This Agreement is made between Party A and Party B.\n"
                    "Governing law: California.\n"
                    "Termination: either party may terminate with 30 days notice.\n"
                    "```\n"
                ),
                attachments=[],
            )
        )
        await agent.monologue()

        gate_passed = agent.context.get_output_data(LEGALFLOW_REVIEW_GATE_KEY)
        assert gate_passed["status"] == "passed"

        monkeypatch.setattr(
            persist_chat, "export_json_chat", lambda ctx: '{"ok": true}', raising=True
        )
        with app.test_request_context(
            "/chat_export", method="POST", json={"ctxid": agent.context.id}
        ):
            ok = await handler.process({"ctxid": agent.context.id}, request)
            assert isinstance(ok, dict)
            assert ok["content"] == '{"ok": true}'
    finally:
        AgentContext.remove(agent.context.id)
