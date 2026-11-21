from helpers.tool_policy import ensure_tool_allowed
from plugins._a0_connector.tools.code_execution_remote import CodeExecutionRemote


class InputRemote(CodeExecutionRemote):
    _allow_running = True

    async def execute(self, keyboard="", **kwargs):
        ensure_tool_allowed(
            self.agent, "code_execution_remote",
            canonical_id="plugin:_a0_connector:code_execution_remote",
            action="terminal",
        )
        self.args = {
            "runtime": "terminal",
            "code": keyboard.rstrip(),
            "session": self.args.get("session", 0),
        }
        return await super().execute(**kwargs)

    def get_heading(self, text=""):
        return f"icon://keyboard input_remote [{self.args.get('session', 0)}]"
