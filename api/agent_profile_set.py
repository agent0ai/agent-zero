from agent import Agent, AgentContext
from helpers import subagents
from helpers.api import ApiHandler, Request, Response
from helpers.persist_chat import save_tmp_chat
from helpers.state_monitor_integration import mark_dirty_for_context
from initialize import initialize_agent


def _agent_profile_labels() -> dict[str, str]:
    return {
        str(item.get("key") or ""): str(item.get("label") or item.get("key") or "")
        for item in subagents.get_all_agents_list()
        if item.get("key")
    }


class SetAgentProfile(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        context_id = str(input.get("context_id", "") or "").strip()
        profile = str(input.get("agent_profile", "") or "").strip()

        if not context_id:
            return Response(status=400, response="Missing context_id")
        if not profile:
            return Response(status=400, response="Missing agent_profile")

        context = AgentContext.get(context_id)
        if not context:
            return Response(status=404, response="Context not found")
        if context.is_running():
            return Response(
                status=409,
                response="Agent profile can be changed after the current run finishes.",
            )

        labels = _agent_profile_labels()
        if profile not in labels:
            return Response(status=404, response=f"Agent profile '{profile}' not found")

        config = initialize_agent(override_settings={"agent_profile": profile})
        context.config = config

        agent = context.agent0
        while agent:
            agent.config = config
            agent = agent.get_data(Agent.DATA_NAME_SUBORDINATE)

        save_tmp_chat(context)
        mark_dirty_for_context(context.id, reason="agent_profile_change")
        return {
            "ok": True,
            "agent_profile": profile,
            "agent_profile_label": labels.get(profile, profile),
        }
