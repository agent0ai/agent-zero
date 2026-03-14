from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

from agent import Agent, LoopData
from python.helpers.errors import RepairableException
from python.helpers.print_style import PrintStyle
from python.helpers.strings import sanitize_string


@dataclass
class Response:
    message: str
    break_loop: bool
    additional: dict[str, Any] | None = None


class Tool:
    # Metadata for the execution engine
    parallel_safe: bool = False

    def __init__(
        self,
        agent: Agent,
        name: str,
        method: str | None,
        args: dict[str, str],
        message: str,
        loop_data: LoopData | None,
        **kwargs,
    ) -> None:
        self.agent = agent
        self.name = name
        self.method = method
        self.args = args
        self.loop_data = loop_data
        self.message = message
        self.progress: str = ""

    @abstractmethod
    async def execute(self, **kwargs) -> Response:
        pass

    def set_progress(self, content: str | None):
        self.progress = content or ""

    def add_progress(self, content: str | None):
        if not content:
            return
        self.progress += content

    async def before_execution(self, **kwargs):
        PrintStyle(font_color="#1B4F72", padding=True, background_color="white", bold=True).print(
            f"{self.agent.agent_name}: Using tool '{self.name}'"
        )
        self.log = self.get_log_object()
        if self.args and isinstance(self.args, dict):
            for key, value in self.args.items():
                PrintStyle(font_color="#85C1E9", bold=True).stream(self.nice_key(key) + ": ")
                PrintStyle(font_color="#85C1E9", padding=isinstance(value, str) and "\n" in value).stream(value)
                PrintStyle().print()

    async def after_execution(self, response: Response, **kwargs):
        text = sanitize_string(response.message.strip())
        self.agent.hist_add_tool_result(self.name, text, **(response.additional or {}))
        PrintStyle(font_color="#1B4F72", background_color="white", padding=True, bold=True).print(
            f"{self.agent.agent_name}: Response from tool '{self.name}'"
        )
        PrintStyle(font_color="#85C1E9").print(text)
        self.log.update(content=text)

    def get_log_object(self):
        if self.method:
            heading = f"icon://construction {self.agent.agent_name}: Using tool '{self.name}:{self.method}'"
        else:
            heading = f"icon://construction {self.agent.agent_name}: Using tool '{self.name}'"
        return self.agent.context.log.log(type="tool", heading=heading, content="", kvps=self.args)

    def nice_key(self, key: str):
        words = key.split("_")
        words = [words[0].capitalize()] + [word.lower() for word in words[1:]]
        result = " ".join(words)
        return result

    def handle_exception(self, error: Exception):
        """Default tool-level exception handling.

        Ensures all tool classes can safely surface errors without crashing
        the monologue loop.
        """
        if isinstance(error, RepairableException):
            message = f"Tool '{self.name}' needs input/config update: {error}"
        else:
            message = f"Tool '{self.name}' failed: {error}"

        self.agent.context.log.log(
            type="error",
            heading=f"{self.agent.agent_name}: Tool '{self.name}' failed",
            content=message,
        )
        self.agent.hist_add_warning(message)
        return Response(message=message, break_loop=True)
