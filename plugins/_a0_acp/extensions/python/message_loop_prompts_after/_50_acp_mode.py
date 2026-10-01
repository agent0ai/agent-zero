from agent import LoopData
from helpers.extension import Extension


_MODE_PROMPTS = {
    "plan": "ACP session mode: plan first. Prefer analysis and tradeoffs. Do not modify files unless the user explicitly asks.",
    "act": "ACP session mode: act. Complete actionable work end-to-end with focused implementation and validation.",
}


class AcpMode(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent or not self.agent.context.get_data("acp_session"):
            return
        prompt = _MODE_PROMPTS.get(str(self.agent.context.get_data("acp_mode") or ""))
        if prompt:
            loop_data.extras_temporary["acp_mode"] = prompt
