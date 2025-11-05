from python.helpers.extension import Extension
from agent import LoopData

class IncludeAgentInfo(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):

        # Get max depth from config
        max_depth = getattr(self.agent.config, 'max_agent_depth', 5)
        remaining_depth = max_depth - self.agent.number

        # Generate subordinate warning if applicable
        subordinate_warning = ""
        if self.agent.number > 0:
            subordinate_warning = (
                "\nWARNING: You are a subordinate agent. Focus on your assigned subtask. "
                "Do NOT delegate your core task to another subordinate with the same profile.\n"
            )

        # Generate depth warning if near limit
        depth_warning = ""
        if remaining_depth <= 1:
            depth_warning = (
                f"\nWARNING: You are near the maximum delegation depth ({self.agent.number}/{max_depth}). "
                "Avoid creating more subordinates unless absolutely necessary.\n"
            )

        # read prompt
        agent_info_prompt = self.agent.read_prompt(
            "agent.extras.agent_info.md",
            number=self.agent.number,
            profile=self.agent.config.profile or "Default",
            max_depth=max_depth,
            remaining_depth=remaining_depth,
            subordinate_warning=subordinate_warning,
            depth_warning=depth_warning,
        )

        # add agent info to the prompt
        loop_data.extras_temporary["agent_info"] = agent_info_prompt
