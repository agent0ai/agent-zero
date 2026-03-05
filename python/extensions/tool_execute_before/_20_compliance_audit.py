from python.helpers.extension import Extension
from python.helpers.compliance import audit_tool_use
from agent import LoopData


class ComplianceToolAudit(Extension):
    """Audit log every tool invocation for JSIG/RMF compliance (AU-12)."""

    async def execute(self, tool_name: str = "", tool_args: dict = {}, loop_data: LoopData = LoopData(), **kwargs):
        agent_id = f"agent{self.agent.number}"
        audit_tool_use(tool_name=tool_name, tool_args=tool_args, agent_id=agent_id)
