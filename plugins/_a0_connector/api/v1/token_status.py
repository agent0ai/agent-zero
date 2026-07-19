"""POST /api/plugins/_a0_connector/v1/token_status."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


class TokenStatus(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from agent import Agent, AgentContext

        context_id = str(
            input.get("context", input.get("context_id", input.get("ctxid", "")))
        ).strip()
        if not context_id:
            return Response(
                response='{"error":"context_id required"}',
                status=400,
                mimetype="application/json",
            )

        context = AgentContext.get(context_id)
        if context is None:
            return Response(
                response='{"error":"Context not found"}',
                status=404,
                mimetype="application/json",
            )

        agent = context.streaming_agent or context.agent0
        window = agent.get_data(Agent.DATA_NAME_CTX_WINDOW) if agent is not None else None
        token_count: int | None = None
        if isinstance(window, dict):
            raw_tokens = window.get("tokens")
            try:
                token_count = int(raw_tokens)
            except (TypeError, ValueError):
                token_count = None

        # ctx_window is only refreshed inside prepare_prompt (LLM turns). After load or
        # between runs it is often missing while history already holds the conversation.
        if token_count is None and agent is not None:
            try:
                from helpers import tokens as tokens_helper
                from helpers.history import output_text

                history_output = agent.history.output()
                full_text = output_text(
                    history_output, ai_label="assistant", human_label="user"
                )
                if full_text.strip():
                    token_count = tokens_helper.approximate_tokens(full_text)
            except Exception:
                token_count = None

        context_window: int | None = None
        try:
            from plugins._model_config.helpers.model_config import get_chat_model_config

            chat_config = get_chat_model_config(agent)
            if isinstance(chat_config, dict):
                raw_context_window = int(chat_config.get("ctx_length", 0))
                if raw_context_window > 0:
                    context_window = raw_context_window
        except Exception:
            context_window = None

        return {
            "ok": True,
            "context_id": context_id,
            "token_count": token_count,
            "context_window": context_window,
        }
