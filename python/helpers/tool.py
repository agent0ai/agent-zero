import inspect
from abc import abstractmethod
from dataclasses import dataclass

from agent import Agent, LoopData
from python.helpers.print_style import PrintStyle
from python.helpers.strings import sanitize_string


# @dataclass
# class Response:
#     message:str
#     break_loop: bool

# class Tool:

#     def __init__(
#         self,
#         message,
#         break_loop=False,
#         output_format="text",
#         pii_mask=False,
#         cache=False,
#         open_window=None,
#     ):
#         self.message = message
#         self.break_loop = break_loop
#         self.output_format = output_format
#         self.pii_mask = pii_mask
#         self.cache = cache
#         self.open_window = open_window

#     def to_dict(self):
#         return {
#             "message": self.message,
#             "break_loop": self.break_loop,
#             "output_format": self.output_format,
#             "pii_mask": self.pii_mask,
#             "cache": self.cache,
#             "open_window": self.open_window,
#         }

class Tool:
    def __init__(self, agent, **kwargs):
        from agent import Agent
        self.agent: Agent = agent
        self.args = kwargs
        self.log = self.get_log_object()
        
    async def execute(self, **kwargs):
        raise NotImplementedError

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading="Calling Tool",
            content=f"Calling tool: {self.__class__.__name__}",
            kvps=self.args,
        )

    def update_progress(self, progress):
        self.log.update(progress=progress)
        self.agent.context.log.set_progress(progress)

class Response:
    def __init__(
        self,
        message,
        break_loop=False,
        output_format="text",
        pii_mask=True,
        cache=False,
        open_window=None,
    ):
        self.message = message
        self.break_loop = break_loop
        self.output_format = output_format
        self.pii_mask = pii_mask
        self.cache = cache
        self.open_window = open_window

    def to_dict(self):
        return {
            "message": self.message,
            "break_loop": self.break_loop,
            "output_format": self.output_format,
            "pii_mask": self.pii_mask,
            "cache": self.cache,
            "open_window": self.open_window,
        }

# Decorator to register a class as a tool
def tool(name, **kwargs):
    def decorator(cls):
        cls.tool_name = name
        cls.tool_data = kwargs
        return cls

    return decorator


# Get all tools from a module
def get_tools(module):
    tools = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and hasattr(obj, "tool_name"):
            tools.append(obj)
    return tools

    # @abstractmethod
    # async def execute(self,**kwargs) -> Response:
    #     pass

    # async def before_execution(self, **kwargs):
    #     PrintStyle(font_color="#1B4F72", padding=True, background_color="white", bold=True).print(f"{self.agent.agent_name}: Using tool '{self.name}'")
    #     self.log = self.get_log_object()
    #     if self.args and isinstance(self.args, dict):
    #         for key, value in self.args.items():
    #             PrintStyle(font_color="#85C1E9", bold=True).stream(self.nice_key(key)+": ")
    #             PrintStyle(font_color="#85C1E9", padding=isinstance(value,str) and "\n" in value).stream(value)
    #             PrintStyle().print()

    # async def after_execution(self, response: Response, **kwargs):
    #     text = sanitize_string(response.message.strip())
    #     self.agent.hist_add_tool_result(self.name, text)
    #     PrintStyle(font_color="#1B4F72", background_color="white", padding=True, bold=True).print(f"{self.agent.agent_name}: Response from tool '{self.name}'")
    #     PrintStyle(font_color="#85C1E9").print(text)
    #     self.log.update(content=text)

    # def get_log_object(self):
    #     if self.method:
    #         heading = f"icon://construction {self.agent.agent_name}: Using tool '{self.name}:{self.method}'"
    #     else:
    #         heading = f"icon://construction {self.agent.agent_name}: Using tool '{self.name}'"
    #     return self.agent.context.log.log(type="tool", heading=heading, content="", kvps=self.args)

    # def nice_key(self, key:str):
    #     words = key.split('_')
    #     words = [words[0].capitalize()] + [word.lower() for word in words[1:]]
    #     result = ' '.join(words)
    #     return result
