from typing import TYPE_CHECKING

from python.helpers import subagents
from python.helpers.api import ApiHandler, Input, Output, Request, Response

if TYPE_CHECKING:
    from python.helpers import projects


class Subagents(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "")
        ctxid = input.get("context_id", None)

        if ctxid:
            _context = self.use_context(ctxid)

        try:
            if action == "list":
                data = self.get_subagents_list()
            elif action == "load":
                data = self.load_agent(input.get("name", None))
            elif action == "save":
                data = self.save_agent(input.get("name", None), input.get("data", None))
            elif action == "delete":
                data = self.delete_agent(input.get("name", None))
            else:
                raise Exception("Invalid action")

            return {
                "ok": True,
                "data": data,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
            }

    def get_subagents_list(self):
        return subagents.get_agents_list()

    def load_agent(self, name: str | None):
        if name is None:
            raise Exception("Subagent name is required")
        return subagents.load_agent_data(name)

    def save_agent(self, name: str | None, data: dict | None):
        if name is None:
            raise Exception("Subagent name is required")
        if data is None:
            raise Exception("Subagent data is required")
        subagent = subagents.SubAgent(**data)
        subagents.save_agent_data(name, subagent)
        return subagents.load_agent_data(name)

    def delete_agent(self, name: str | None):
        if name is None:
            raise Exception("Subagent name is required")
        subagents.delete_agent_data(name)
