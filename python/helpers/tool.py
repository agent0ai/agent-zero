from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

from agent import Agent, LoopData
from python.helpers.print_style import PrintStyle
from python.helpers.strings import sanitize_string
from python.helpers.audit_log import extract_urls, log_event


@dataclass
class Response:
    message:str
    break_loop: bool
    additional: dict[str, Any] | None = None

class Tool:

    def __init__(self, agent: Agent, name: str, method: str | None, args: dict[str,str], message: str, loop_data: LoopData | None, **kwargs) -> None:
        self.agent = agent
        self.name = name
        self.method = method
        self.args = args
        self.loop_data = loop_data
        self.message = message
        self.progress: str = ""

    @abstractmethod
    async def execute(self,**kwargs) -> Response:
        pass

    def set_progress(self, content: str | None):
        self.progress = content or ""

    def add_progress(self, content: str | None):
        if not content:
            return
        self.progress += content

    async def before_execution(self, **kwargs):
        PrintStyle(font_color="#1B4F72", padding=True, background_color="white", bold=True).print(f"{self.agent.agent_name}: Using tool '{self.name}'")
        self.log = self.get_log_object()
        if self.args and isinstance(self.args, dict):
            for key, value in self.args.items():
                PrintStyle(font_color="#85C1E9", bold=True).stream(self.nice_key(key)+": ")
                PrintStyle(font_color="#85C1E9", padding=isinstance(value,str) and "\n" in value).stream(value)
                PrintStyle().print()

    async def after_execution(self, response: Response, **kwargs):
        text = sanitize_string(response.message.strip())

        if self.name in {"search_engine", "knowledge", "knowledge_tool"}:
            try:
                urls = extract_urls(text)
                sources: list[str] = urls
                if not sources and isinstance(self.args, dict):
                    q = self.args.get("query") or self.args.get("question")
                    if q:
                        sources = [q]
                log_event(
                    agent_role=str(getattr(self.agent, "agent_name", "agent")),
                    user_action=f"tool:{self.name}",
                    sources=sources,
                    output=text,
                    file_paths_touched=[],
                    extra={"tool_args": dict(self.args or {})},
                )
            except Exception:
                # Audit logging must never break the tool flow.
                pass

        self.agent.hist_add_tool_result(self.name, text, **(response.additional or {}))
        PrintStyle(font_color="#1B4F72", background_color="white", padding=True, bold=True).print(f"{self.agent.agent_name}: Response from tool '{self.name}'")
        PrintStyle(font_color="#85C1E9").print(text)
        self.log.update(content=text)

    def get_log_object(self):
        if self.method:
            heading = f"icon://construction {self.agent.agent_name}: Using tool '{self.name}:{self.method}'"
        else:
            heading = f"icon://construction {self.agent.agent_name}: Using tool '{self.name}'"
        return self.agent.context.log.log(type="tool", heading=heading, content="", kvps=self.args, _tool_name=self.name)

    def nice_key(self, key:str):
        words = key.split('_')
        words = [words[0].capitalize()] + [word.lower() for word in words[1:]]
        result = ' '.join(words)
        return result
