from agent import Agent, UserMessage
from python.helpers.tool import Tool, Response
import asyncio
from python.helpers.defer import DeferredTask


class SubordinateBroadcast(Tool):

    async def execute(self, message: str = "", **kwargs) -> Response:
        if not isinstance(message, str) or not message.strip():
            return Response(message="No message provided for broadcast.", break_loop=False)

        # Retrieve subordinate mapping
        subordinates: dict[str, Agent] = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE) or {}
        if not subordinates:
            return Response(message="No subordinates available to broadcast to.", break_loop=False)

        # Optional targeting by profile(s)
        def parse_profiles(val) -> list[str]:
            if isinstance(val, list):
                return [str(p).strip() for p in val if str(p).strip() != ""]
            s = str(val or "").strip()
            if not s:
                return []
            if "," in s:
                return [p.strip() for p in s.split(",") if p.strip()]
            return [s]

        profiles_input = (
            kwargs.get(
                "settings_profiles",
                kwargs.get(
                    "settings_profile",
                    kwargs.get(
                        "agent_profiles",
                        kwargs.get("agent_profile", []),
                    ),
                ),
            )
        )
        target_profiles: list[str] = parse_profiles(profiles_input)
        if target_profiles:
            # Filter only matching existing subordinates
            subordinates = {k: v for k, v in subordinates.items() if k in target_profiles}
            if not subordinates:
                return Response(message="No matching subordinates for the specified profiles.", break_loop=False)

        attachments = kwargs.get("attachments", []) or []

        # Start or reuse background tasks per subordinate
        task_pairs: list[tuple[str, DeferredTask | None]] = []
        for profile_key, subordinate in list(subordinates.items()):
            try:
                subordinate.hist_add_user_message(UserMessage(message=message, attachments=attachments))
                if subordinate.context.task and subordinate.context.task.is_alive():
                    task = subordinate.context.task
                else:
                    task = subordinate.context.run_task(subordinate.monologue)
                task_pairs.append((profile_key, task))
            except Exception:
                task_pairs.append((profile_key, None))

        async def await_result(t: DeferredTask | None):
            if t is None:
                return "Error: Failed to start task"
            try:
                return await t.result()
            except Exception as e:
                return f"Error: {e}"

        results = await asyncio.gather(*[await_result(t) for _, t in task_pairs])

        # Aggregate with profile prefix
        formatted = []
        for (profile_key, _), resp in zip(task_pairs, results):
            profile_label = profile_key or "default"
            formatted.append(f"[{profile_label}]\n{resp}")

        joined = "\n\n".join(formatted) if formatted else "(no responses)"
        return Response(message=joined, break_loop=False)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://communication {self.agent.agent_name}: Broadcast to Subordinates",
            content="",
            kvps=self.args,
        )
