from agent import Agent, UserMessage
from python.helpers.tool import Tool, Response
from python.tools.code_execution_tool import CodeExecution


CONTROL_CHAR_MAP = {
    "<ctrl+c>": "\x03",  # ETX - Interrupt (SIGINT)
    "<ctrl+d>": "\x04",  # EOT - End of transmission (EOF)
}


class Input(Tool):

    async def execute(self, keyboard="", **kwargs):
        # normalize keyboard input
        keyboard = keyboard.rstrip()
        display_code = keyboard
        keyboard = resolve_control_chars(keyboard)
        # keyboard += "\n" # no need to, code_exec does that
        
        # terminal session number
        session = int(self.args.get("session", 0))

        # forward keyboard input to code execution tool
        args = {
            "runtime": "terminal",
            "code": keyboard,
            "session": session,
            "allow_running": True,
            "source": "input",
            "display_code": display_code,
        }
        cet = CodeExecution(
            self.agent, "code_execution_tool", "", args, self.message, self.loop_data
        )
        cet.log = self.log
        return await cet.execute(**args)

    def get_log_object(self):
        return self.agent.context.log.log(type="code_exe", heading=f"icon://keyboard {self.agent.agent_name}: Using tool '{self.name}'", content="", kvps=self.args)

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message, **(response.additional or {}))


def resolve_control_chars(text: str) -> str:
    result = text
    for placeholder, byte_value in CONTROL_CHAR_MAP.items():
        if placeholder in result:
            result = result.replace(placeholder, byte_value)
    return result
