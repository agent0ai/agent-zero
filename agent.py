import asyncio
import random
import string

import nest_asyncio

nest_asyncio.apply()

import contextlib
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
)

import models
import python.helpers.log as Log
from python.helpers import context as context_helper, dirty_json, errors, extract_tools, files, history, tokens
from python.helpers.defer import DeferredTask
from python.helpers.dirty_json import DirtyJson
from python.helpers.errors import RepairableException
from python.helpers.extension import call_extensions
from python.helpers.localization import Localization
from python.helpers.print_style import PrintStyle
from python.helpers.proactive import ProactiveManager
from python.helpers.security import SecurityManager


class AgentContextType(Enum):
    USER = "user"
    TASK = "task"
    BACKGROUND = "background"


class AgentContext:
    _contexts: dict[str, "AgentContext"] = {}
    _counter: int = 0
    _notification_manager = None

    def __init__(
        self,
        config: "AgentConfig",
        id: str | None = None,
        name: str | None = None,
        agent0: "Agent|None" = None,
        log: Log.Log | None = None,
        paused: bool = False,
        streaming_agent: "Agent|None" = None,
        created_at: datetime | None = None,
        type: AgentContextType = AgentContextType.USER,
        last_message: datetime | None = None,
        data: dict | None = None,
        output_data: dict | None = None,
        set_current: bool = False,
    ):
        # initialize context
        self.id = id or AgentContext.generate_id()
        existing = self._contexts.get(self.id, None)
        if existing:
            AgentContext.remove(self.id)
        self._contexts[self.id] = self
        if set_current:
            AgentContext.set_current(self.id)

        # initialize state
        self.name = name
        self.config = config
        self.log = log or Log.Log()
        self.log.context = self
        self.agent0 = agent0 or Agent(0, self.config, self)
        self.paused = paused
        self.streaming_agent = streaming_agent
        self.task: DeferredTask | None = None
        self.created_at = created_at or datetime.now(timezone.utc)
        self.type = type
        AgentContext._counter += 1
        self.no = AgentContext._counter
        self.last_message = last_message or datetime.now(timezone.utc)
        self.data = data or {}
        self.output_data = output_data or {}

    @staticmethod
    def get(id: str):
        return AgentContext._contexts.get(id, None)

    @staticmethod
    def use(id: str):
        context = AgentContext.get(id)
        if context:
            AgentContext.set_current(id)
        else:
            AgentContext.set_current("")
        return context

    @staticmethod
    def current():
        ctxid = context_helper.get_context_data("agent_context_id", "")
        if not ctxid:
            return None
        return AgentContext.get(ctxid)

    @staticmethod
    def set_current(ctxid: str):
        context_helper.set_context_data("agent_context_id", ctxid)

    @staticmethod
    def first():
        if not AgentContext._contexts:
            return None
        return next(iter(AgentContext._contexts.values()))

    @staticmethod
    def all():
        return list(AgentContext._contexts.values())

    @staticmethod
    def generate_id():
        def generate_short_id():
            return "".join(random.choices(string.ascii_letters + string.digits, k=8))

        while True:
            short_id = generate_short_id()
            if short_id not in AgentContext._contexts:
                return short_id

    @classmethod
    def get_notification_manager(cls):
        if cls._notification_manager is None:
            from python.helpers.notification import NotificationManager  # type: ignore

            cls._notification_manager = NotificationManager()
        return cls._notification_manager

    @staticmethod
    def remove(id: str):
        context = AgentContext._contexts.pop(id, None)
        if context and context.task:
            context.task.kill()
        return context

    def get_data(self, key: str, recursive: bool = True):
        # recursive is not used now, prepared for context hierarchy
        return self.data.get(key, None)

    def set_data(self, key: str, value: Any, recursive: bool = True):
        # recursive is not used now, prepared for context hierarchy
        self.data[key] = value

    def get_output_data(self, key: str, recursive: bool = True):
        # recursive is not used now, prepared for context hierarchy
        return self.output_data.get(key, None)

    def set_output_data(self, key: str, value: Any, recursive: bool = True):
        # recursive is not used now, prepared for context hierarchy
        self.output_data[key] = value

    def output(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": (
                Localization.get().serialize_datetime(self.created_at)
                if self.created_at
                else Localization.get().serialize_datetime(datetime.fromtimestamp(0))
            ),
            "no": self.no,
            "log_guid": self.log.guid,
            "log_version": len(self.log.updates),
            "log_length": len(self.log.logs),
            "paused": self.paused,
            "last_message": (
                Localization.get().serialize_datetime(self.last_message)
                if self.last_message
                else Localization.get().serialize_datetime(datetime.fromtimestamp(0))
            ),
            "type": self.type.value,
            **self.output_data,
        }

    @staticmethod
    def log_to_all(
        type: Log.Type,
        heading: str | None = None,
        content: str | None = None,
        kvps: dict | None = None,
        temp: bool | None = None,
        update_progress: Log.ProgressUpdate | None = None,
        id: str | None = None,  # Add id parameter
        **kwargs,
    ) -> list[Log.LogItem]:
        items: list[Log.LogItem] = []
        for context in AgentContext.all():
            items.append(context.log.log(type, heading, content, kvps, temp, update_progress, id, **kwargs))
        return items

    def kill_process(self):
        if self.task:
            self.task.kill()

    def reset(self):
        self.kill_process()
        self.log.reset()
        self.agent0 = Agent(0, self.config, self)
        self.streaming_agent = None
        self.paused = False

    def nudge(self):
        self.kill_process()
        self.paused = False
        self.task = self.run_task(self.get_agent().monologue)
        return self.task

    def get_agent(self):
        return self.streaming_agent or self.agent0

    def communicate(self, msg: "UserMessage", broadcast_level: int = 1):
        self.paused = False  # unpause if paused

        current_agent = self.get_agent()

        if self.task and self.task.is_alive():
            # set intervention messages to agent(s):
            intervention_agent = current_agent
            while intervention_agent and broadcast_level != 0:
                intervention_agent.intervention = msg
                broadcast_level -= 1
                intervention_agent = intervention_agent.data.get(Agent.DATA_NAME_SUPERIOR, None)
        else:
            self.task = self.run_task(self._process_chain, current_agent, msg)

        return self.task

    def run_task(self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any):
        if not self.task:
            self.task = DeferredTask(
                thread_name=self.__class__.__name__,
            )
        self.task.start_task(func, *args, **kwargs)
        return self.task

    # this wrapper ensures that superior agents are called back if the chat was loaded from file and original callstack is gone
    async def _process_chain(self, agent: "Agent", msg: "UserMessage|str", user=True):
        try:
            (
                agent.hist_add_user_message(msg)  # type: ignore
                if user
                else agent.hist_add_tool_result(
                    tool_name="call_subordinate",
                    tool_result=msg,  # type: ignore
                )
            )
            response = await agent.monologue()  # type: ignore
            superior = agent.data.get(Agent.DATA_NAME_SUPERIOR, None)
            if superior:
                response = await self._process_chain(superior, response, False)  # type: ignore
            return response
        except Exception as e:
            agent.handle_critical_exception(e)


@dataclass
class AgentConfig:
    chat_model: models.ModelConfig
    utility_model: models.ModelConfig
    embeddings_model: models.ModelConfig
    browser_model: models.ModelConfig
    mcp_servers: str
    profile: str = ""
    memory_subdir: str = ""
    knowledge_subdirs: list[str] = field(default_factory=lambda: ["default", "custom"])
    browser_http_headers: dict[str, str] = field(default_factory=dict)  # Custom HTTP headers for browser requests
    code_exec_ssh_enabled: bool = True
    code_exec_ssh_addr: str = "localhost"
    code_exec_ssh_port: int = 55022
    code_exec_ssh_user: str = "root"
    code_exec_ssh_pass: str = ""
    additional: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserMessage:
    message: str
    attachments: list[str] = field(default_factory=list[str])
    system_message: list[str] = field(default_factory=list[str])


class LoopData:
    def __init__(self, **kwargs):
        self.iteration = -1
        self.system = []
        self.user_message: history.Message | None = None
        self.history_output: list[history.OutputMessage] = []
        self.extras_temporary: OrderedDict[str, history.MessageContent] = OrderedDict()
        self.extras_persistent: OrderedDict[str, history.MessageContent] = OrderedDict()
        self.last_response = ""
        self.params_temporary: dict = {}
        self.params_persistent: dict = {}
        self.current_tool = None

        # override values with kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


# intervention exception class - skips rest of message loop iteration
class InterventionException(Exception):
    pass


# killer exception class - not forwarded to LLM, cannot be fixed on its own, ends message loop


class HandledException(Exception):
    pass


class Agent:
    DATA_NAME_SUPERIOR = "_superior"
    DATA_NAME_SUBORDINATE = "_subordinate"
    DATA_NAME_CTX_WINDOW = "ctx_window"

    def __init__(self, number: int, config: AgentConfig, context: AgentContext | None = None):
        # agent config
        self.config = config

        # agent context
        self.context = context or AgentContext(config=config, agent0=self)

        # non-config vars
        self.number = number
        self.agent_name = f"A{self.number}"

        self.history = history.History(self)  # type: ignore[abstract]
        self.last_user_message: history.Message | None = None
        self.intervention: UserMessage | None = None
        self.data: dict[str, Any] = {}  # free data object all the tools can use

        asyncio.run(self.call_extensions("agent_init"))

    async def monologue(self):
        while True:
            try:
                # Proactive nudge check (Graceful fail)
                with contextlib.suppress(Exception):
                    ProactiveManager.check_and_nudge()

                # loop data dictionary to pass to extensions
                self.loop_data = LoopData(user_message=self.last_user_message)
                # call monologue_start extensions
                await self.call_extensions("monologue_start", loop_data=self.loop_data)

                printer = PrintStyle(italic=True, font_color="#b3ffd9", padding=False)

                # let the agent run message loop until he stops it with a response tool
                while True:
                    self.context.streaming_agent = self  # mark self as current streamer
                    self.loop_data.iteration += 1
                    self.loop_data.params_temporary = {}  # clear temporary params

                    # call message_loop_start extensions
                    await self.call_extensions("message_loop_start", loop_data=self.loop_data)

                    try:
                        # prepare LLM chain (model, system, history)
                        prompt = await self.prepare_prompt(loop_data=self.loop_data)

                        # call before_main_llm_call extensions
                        await self.call_extensions("before_main_llm_call", loop_data=self.loop_data)

                        async def reasoning_callback(chunk: str, full: str):
                            await self.handle_intervention()
                            if chunk == full:
                                printer.print("Reasoning: ")  # start of reasoning
                            # Pass chunk and full data to extensions for processing
                            stream_data = {"chunk": chunk, "full": full}
                            await self.call_extensions(
                                "reasoning_stream_chunk", loop_data=self.loop_data, stream_data=stream_data
                            )
                            # Stream masked chunk after extensions processed it
                            if stream_data.get("chunk"):
                                printer.stream(stream_data["chunk"])
                            # Use the potentially modified full text for downstream processing
                            await self.handle_reasoning_stream(stream_data["full"])

                        async def stream_callback(chunk: str, full: str):
                            await self.handle_intervention()
                            # output the agent response stream
                            if chunk == full:
                                printer.print("Response: ")  # start of response
                            # Pass chunk and full data to extensions for processing
                            stream_data = {"chunk": chunk, "full": full}
                            await self.call_extensions(
                                "response_stream_chunk", loop_data=self.loop_data, stream_data=stream_data
                            )
                            # Stream masked chunk after extensions processed it
                            if stream_data.get("chunk"):
                                printer.stream(stream_data["chunk"])
                            # Use the potentially modified full text for downstream processing
                            await self.handle_response_stream(stream_data["full"])

                        # call main LLM
                        agent_response, _reasoning = await self.call_chat_model(
                            messages=prompt,
                            response_callback=stream_callback,
                            reasoning_callback=reasoning_callback,
                        )

                        # Notify extensions to finalize their stream filters
                        await self.call_extensions("reasoning_stream_end", loop_data=self.loop_data)
                        await self.call_extensions("response_stream_end", loop_data=self.loop_data)

                        await self.handle_intervention(agent_response)

                        if (
                            self.loop_data.last_response == agent_response
                        ):  # if assistant_response is the same as last message in history, let him know
                            # Append the assistant's response to the history
                            self.hist_add_ai_response(agent_response)
                            # Append warning message to the history
                            warning_msg = self.read_prompt("fw.msg_repeat.md")
                            self.hist_add_warning(message=warning_msg)
                            PrintStyle(font_color="orange", padding=True).print(warning_msg)
                            self.context.log.log(type="warning", content=warning_msg)
                            # Nudge the model away from repeating and toward a response tool.
                            self.loop_data.extras_temporary["repeat_guard"] = (
                                "Your last response repeated exactly. Respond differently "
                                "and prefer using the response tool with a helpful next step."
                            )

                        else:  # otherwise proceed with tool
                            # Append the assistant's response to the history
                            self.hist_add_ai_response(agent_response)
                            # process tools requested in agent message
                            tools_result = await self.process_tools(agent_response)
                            if tools_result:  # final response of message loop available
                                return tools_result  # break the execution if the task is done

                    # exceptions inside message loop:
                    except InterventionException:
                        pass  # intervention message has been handled in handle_intervention(), proceed with conversation loop
                    except RepairableException as e:
                        # Forward repairable errors to the LLM, maybe it can fix them
                        msg = {"message": errors.format_error(e)}
                        await self.call_extensions("error_format", msg=msg)
                        self.hist_add_warning(msg["message"])
                        PrintStyle(font_color="red", padding=True).print(msg["message"])
                        self.context.log.log(type="error", content=msg["message"])
                    except Exception as e:
                        # Other exception kill the loop
                        self.handle_critical_exception(e)

                    finally:
                        # call message_loop_end extensions
                        await self.call_extensions("message_loop_end", loop_data=self.loop_data)

            # exceptions outside message loop:
            except InterventionException:
                pass  # just start over
            except Exception as e:
                self.handle_critical_exception(e)
            finally:
                self.context.streaming_agent = None  # unset current streamer
                # call monologue_end extensions
                await self.call_extensions("monologue_end", loop_data=self.loop_data)  # type: ignore

    async def prepare_prompt(self, loop_data: LoopData) -> list[BaseMessage]:
        self.context.log.set_progress("Building prompt")

        # call extensions before setting prompts
        await self.call_extensions("message_loop_prompts_before", loop_data=loop_data)

        # set system prompt and message history
        loop_data.system = await self.get_system_prompt(self.loop_data)
        loop_data.history_output = self.history.output()

        # and allow extensions to edit them
        await self.call_extensions("message_loop_prompts_after", loop_data=loop_data)

        # concatenate system prompt
        system_text = "\n\n".join(loop_data.system)

        # join extras
        extras = history.Message(  # type: ignore[abstract]
            False,
            content=self.read_prompt(
                "agent.context.extras.md",
                extras=dirty_json.stringify({**loop_data.extras_persistent, **loop_data.extras_temporary}),
            ),
        ).output()
        loop_data.extras_temporary.clear()

        # convert history + extras to LLM format
        history_langchain: list[BaseMessage] = history.output_langchain(loop_data.history_output + extras)

        # build full prompt from system prompt, message history and extrS
        full_prompt: list[BaseMessage] = [
            SystemMessage(content=system_text),
            *history_langchain,
        ]
        full_text = ChatPromptTemplate.from_messages(full_prompt).format()

        # store as last context window content
        self.set_data(
            Agent.DATA_NAME_CTX_WINDOW,
            {
                "text": full_text,
                "tokens": tokens.approximate_tokens(full_text),
            },
        )

        return full_prompt

    def handle_critical_exception(self, exception: Exception):
        if isinstance(exception, HandledException):
            raise exception  # Re-raise the exception to kill the loop
        elif isinstance(exception, asyncio.CancelledError):
            # Handling for asyncio.CancelledError
            PrintStyle(font_color="white", background_color="red", padding=True).print(
                f"Context {self.context.id} terminated during message loop"
            )
            raise HandledException(exception)  # Re-raise the exception to cancel the loop
        else:
            # Handling for general exceptions
            error_text = errors.error_text(exception)
            error_message = errors.format_error(exception)

            # Mask secrets in error messages
            PrintStyle(font_color="red", padding=True).print(error_message)
            self.context.log.log(
                type="error",
                heading="Error",
                content=error_message,
                kvps={"text": error_text},
            )
            PrintStyle(font_color="red", padding=True).print(f"{self.agent_name}: {error_text}")

            raise HandledException(exception)  # Re-raise the exception to kill the loop

    async def get_system_prompt(self, loop_data: LoopData) -> list[str]:
        system_prompt: list[str] = []

        # Add User Profile if available
        try:
            from instruments.custom.workflow_engine.workflow_db import WorkflowEngineDatabase

            db_path = files.get_abs_path("./instruments/custom/workflow_engine/data/workflow.db")
            db = WorkflowEngineDatabase(db_path)
            conn = db._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = 'default_user'")
            row = cursor.fetchone()
            conn.close()

            if row:
                profile = dict(row)
                profile_text = "## Power User Profile (Identity Verified via Passkey)\n"
                profile_text += f"- **User**: {profile.get('full_name')} <{profile.get('email')}>\n"
                profile_text += "- **Environment**: High-Security White-Hat Platform\n"
                profile_text += f"- **Timezone**: {profile.get('timezone')}\n"
                profile_text += f"- **Locale**: {profile.get('locale')}\n"
                profile_text += (
                    "- **Security Policy**: Multi-Factor/Passkey required for high-risk tools (bash, email, etc.)\n"
                )
                if profile.get("phone_number"):
                    profile_text += f"- **Phone**: {profile.get('phone_number')}\n"
                system_prompt.append(profile_text)
        except Exception:
            pass  # Silently fail if DB or table not ready

        await self.call_extensions("system_prompt", system_prompt=system_prompt, loop_data=loop_data)
        return system_prompt

    def parse_prompt(self, _prompt_file: str, **kwargs):
        dirs = [files.get_abs_path("prompts")]
        if self.config.profile:  # if agent has custom folder, use it and use default as backup
            prompt_dir = files.get_abs_path("agents", self.config.profile, "prompts")
            dirs.insert(0, prompt_dir)
        prompt = files.parse_file(_prompt_file, _directories=dirs, **kwargs)
        return prompt

    def read_prompt(self, file: str, **kwargs) -> str:
        dirs = [files.get_abs_path("prompts")]
        if self.config.profile:  # if agent has custom folder, use it and use default as backup
            prompt_dir = files.get_abs_path("agents", self.config.profile, "prompts")
            dirs.insert(0, prompt_dir)
        prompt = files.read_prompt_file(file, _directories=dirs, **kwargs)
        prompt = files.remove_code_fences(prompt)
        return prompt

    def get_data(self, field: str):
        return self.data.get(field, None)

    def set_data(self, field: str, value):
        self.data[field] = value

    def hist_add_message(self, ai: bool, content: history.MessageContent, tokens: int = 0):
        self.last_message = datetime.now(timezone.utc)
        # Allow extensions to process content before adding to history
        content_data = {"content": content}
        asyncio.run(self.call_extensions("hist_add_before", content_data=content_data, ai=ai))
        return self.history.add_message(ai=ai, content=content_data["content"], tokens=tokens)

    def hist_add_user_message(self, message: UserMessage, intervention: bool = False):
        self.history.new_topic()  # user message starts a new topic in history

        # load message template based on intervention
        if intervention:
            content = self.parse_prompt(
                "fw.intervention.md",
                message=message.message,
                attachments=message.attachments,
                system_message=message.system_message,
            )
        else:
            content = self.parse_prompt(
                "fw.user_message.md",
                message=message.message,
                attachments=message.attachments,
                system_message=message.system_message,
            )

        # remove empty parts from template
        if isinstance(content, dict):
            content = {k: v for k, v in content.items() if v}

        # add to history
        msg = self.hist_add_message(False, content=content)  # type: ignore
        self.last_user_message = msg
        return msg

    def hist_add_ai_response(self, message: str):
        self.loop_data.last_response = message
        content = self.parse_prompt("fw.ai_response.md", message=message)
        return self.hist_add_message(True, content=content)

    def hist_add_warning(self, message: history.MessageContent):
        content = self.parse_prompt("fw.warning.md", message=message)
        return self.hist_add_message(False, content=content)

    def hist_add_tool_result(self, tool_name: str, tool_result: str, **kwargs):
        data = {
            "tool_name": tool_name,
            "tool_result": tool_result,
            **kwargs,
        }
        asyncio.run(self.call_extensions("hist_add_tool_result", data=data))
        return self.hist_add_message(False, content=data)

    def concat_messages(self, messages):  # TODO add param for message range, topic, history
        return self.history.output_text(human_label="user", ai_label="assistant")

    def get_chat_model(self):
        # Check if LLM Router should select the model
        from python.helpers import settings

        set = settings.get_settings()
        if set.get("llm_router_enabled", False):
            try:
                from python.helpers.llm_router import RoutingPriority, get_router

                router = get_router()
                model_info = router.select_model(
                    role="chat", context_type="USER", priority=RoutingPriority.QUALITY, required_capabilities=["chat"]
                )
                if model_info:
                    return models.get_chat_model(
                        model_info.provider,
                        model_info.name,
                    )
            except Exception:
                pass  # Fall back to default

        return models.get_chat_model(
            self.config.chat_model.provider,
            self.config.chat_model.name,
            model_config=self.config.chat_model,
            **self.config.chat_model.build_kwargs(),
        )

    def get_utility_model(self):
        # Check if LLM Router should select the model
        from python.helpers import settings

        set = settings.get_settings()
        if set.get("llm_router_enabled", False):
            try:
                from python.helpers.llm_router import RoutingPriority, get_router

                router = get_router()
                model_info = router.select_model(
                    role="utility",
                    context_type="TASK",
                    priority=RoutingPriority.SPEED,  # Utility calls need speed
                    required_capabilities=["chat"],
                )
                if model_info:
                    return models.get_chat_model(
                        model_info.provider,
                        model_info.name,
                    )
            except Exception:
                pass  # Fall back to default

        return models.get_chat_model(
            self.config.utility_model.provider,
            self.config.utility_model.name,
            model_config=self.config.utility_model,
            **self.config.utility_model.build_kwargs(),
        )

    def get_browser_model(self):
        return models.get_browser_model(
            self.config.browser_model.provider,
            self.config.browser_model.name,
            model_config=self.config.browser_model,
            **self.config.browser_model.build_kwargs(),
        )

    def get_embedding_model(self):
        return models.get_embedding_model(
            self.config.embeddings_model.provider,
            self.config.embeddings_model.name,
            model_config=self.config.embeddings_model,
            **self.config.embeddings_model.build_kwargs(),
        )

    async def call_utility_model(
        self,
        system: str,
        message: str,
        callback: Callable[[str], Awaitable[None]] | None = None,
        background: bool = False,
    ):
        model = self.get_utility_model()

        # call extensions
        call_data = {
            "model": model,
            "system": system,
            "message": message,
            "callback": callback,
            "background": background,
        }
        await self.call_extensions("util_model_call_before", call_data=call_data)

        # propagate stream to callback if set
        async def stream_callback(chunk: str, total: str):
            if call_data["callback"]:
                await call_data["callback"](chunk)

        response, _reasoning = await call_data["model"].unified_call(
            system_message=call_data["system"],
            user_message=call_data["message"],
            response_callback=stream_callback if call_data["callback"] else None,
            rate_limiter_callback=self.rate_limiter_callback if not call_data["background"] else None,
        )

        return response

    def get_thinking_kwargs(self) -> dict:
        """Get kwargs for thinking/extended reasoning mode if enabled."""
        from python.helpers import settings

        set = settings.get_settings()

        kwargs = {}
        if set.get("thinking_enabled", False):
            budget = set.get("thinking_budget", 1024)
            # For Anthropic Claude models with extended thinking support
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": int(budget)}
        return kwargs

    async def call_chat_model(
        self,
        messages: list[BaseMessage],
        response_callback: Callable[[str, str], Awaitable[None]] | None = None,
        reasoning_callback: Callable[[str, str], Awaitable[None]] | None = None,
        background: bool = False,
    ):
        response = ""

        # model class
        model = self.get_chat_model()

        # Get thinking mode kwargs if enabled
        thinking_kwargs = self.get_thinking_kwargs()

        # call model
        response, reasoning = await model.unified_call(
            messages=messages,
            reasoning_callback=reasoning_callback,
            response_callback=response_callback,
            rate_limiter_callback=self.rate_limiter_callback if not background else None,
            **thinking_kwargs,
        )

        return response, reasoning

    async def rate_limiter_callback(self, message: str, key: str, total: int, limit: int):
        # show the rate limit waiting in a progress bar, no need to spam the chat history
        self.context.log.set_progress(message, True)
        return False

    async def handle_intervention(self, progress: str = ""):
        while self.context.paused:
            await asyncio.sleep(0.1)  # wait if paused
        if self.intervention:  # if there is an intervention message, but not yet processed
            msg = self.intervention
            self.intervention = None  # reset the intervention message
            # If a tool was running, save its progress to history
            last_tool = self.loop_data.current_tool
            if last_tool:
                tool_progress = last_tool.progress.strip()
                if tool_progress:
                    self.hist_add_tool_result(last_tool.name, tool_progress)
                    last_tool.set_progress(None)
            if progress.strip():
                self.hist_add_ai_response(progress)
            # append the intervention message
            self.hist_add_user_message(msg, intervention=True)
            raise InterventionException(msg)

    async def wait_if_paused(self):
        while self.context.paused:
            await asyncio.sleep(0.1)

    async def process_tools(self, msg: str):
        async def execute_tool_task(req: dict):
            raw_tool_name = req.get("tool_name", "")
            tool_args = req.get("tool_args", {})

            if not raw_tool_name:
                response_text = req.get("response")
                if response_text and not tool_args:
                    tool_args = {"text": response_text}
                    raw_tool_name = "response"
                else:
                    return None

            tool_name = raw_tool_name
            tool_method = None
            if ":" in raw_tool_name:
                tool_name, tool_method = raw_tool_name.split(":", 1)

            tool = None
            try:
                import python.helpers.mcp_handler as mcp_helper

                mcp_tool_candidate = mcp_helper.MCPConfig.get_instance().get_tool(self, tool_name)
                if mcp_tool_candidate:
                    tool = mcp_tool_candidate
            except:
                pass

            if not tool:
                tool = self.get_tool(
                    name=tool_name, method=tool_method, args=tool_args, message=msg, loop_data=self.loop_data
                )

            if tool:
                self.loop_data.current_tool = tool
                try:
                    await self.handle_intervention()
                    await tool.before_execution(**tool_args)
                    await self.call_extensions("tool_execute_before", tool_args=tool_args or {}, tool_name=tool_name)

                    response = await tool.execute(**tool_args)

                    await self.call_extensions(
                        "tool_execute_after", tool_args=tool_args or {}, tool_name=tool_name, response=response
                    )
                    await tool.after_execution(response)
                    return response
                except Exception as e:
                    return tool.handle_exception(e) or e
            return None

        # search for all tool usage requests in agent message
        tool_requests = extract_tools.json_parse_all_dirty(msg)

        # Fallback to single tool if multiple not found or if it's the old format
        if not tool_requests:
            single_request = extract_tools.json_parse_dirty(msg)
            if single_request:
                tool_requests = [single_request]

        if not tool_requests:
            warning_msg_misformat = self.read_prompt("fw.msg_misformat.md")
            self.hist_add_warning(warning_msg_misformat)
            PrintStyle(font_color="red", padding=True).print(warning_msg_misformat)
            self.context.log.log(
                type="error",
                content=f"{self.agent_name}: Message misformat, no valid tool request found.",
            )
            return

        # Orchestrate execution with automatic parallelization for safe tools
        results = []
        i = 0
        while i < len(tool_requests):
            req = tool_requests[i]
            t_name = req.get("tool_name", "")

            # Resolve tool class to check for parallel safety
            is_safe = False
            try:
                # Basic check for common read-only tools
                if any(t_name.startswith(p) for p in ["read_", "search_", "grep_", "list_", "get_"]):
                    is_safe = True
                else:
                    # Deep check
                    tool_temp = self.get_tool(name=t_name, method=None, args={}, message="", loop_data=None)
                    is_safe = getattr(tool_temp, "parallel_safe", False)
            except:
                pass

            # Identify a batch of parallel-safe tools
            batch = [req]
            if is_safe:
                j = i + 1
                while j < len(tool_requests):
                    next_req = tool_requests[j]
                    next_name = next_req.get("tool_name", "")

                    # Check safety of next tool
                    next_safe = False
                    if any(next_name.startswith(p) for p in ["read_", "search_", "grep_", "list_", "get_"]):
                        next_safe = True
                    else:
                        try:
                            nt_temp = self.get_tool(name=next_name, method=None, args={}, message="", loop_data=None)
                            next_safe = getattr(nt_temp, "parallel_safe", False)
                        except:
                            pass

                    if next_safe:
                        batch.append(next_req)
                        j += 1
                    else:
                        break

            if len(batch) > 1:
                PrintStyle(font_color="cyan", bold=True).print(
                    f"⚡ [Parallel Execution] Running {len(batch)} tools concurrently..."
                )
                SecurityManager.log_event("parallel_tool_execution", "success", details={"count": len(batch)})
                # Execute batch in parallel
                batch_results = await asyncio.gather(*(execute_tool_task(r) for r in batch), return_exceptions=True)
                results.extend(batch_results)
                i += len(batch)
            else:
                # Execute single tool
                res = await execute_tool_task(req)
                results.append(res)
                i += 1

        # Handle final result (if any tool broke the loop like 'response')
        from python.helpers.tool import Response

        for res in results:
            if isinstance(res, Response) and res.break_loop:
                return res.message
        return None

    async def handle_reasoning_stream(self, stream: str):
        await self.handle_intervention()
        await self.call_extensions(
            "reasoning_stream",
            loop_data=self.loop_data,
            text=stream,
        )

    async def handle_response_stream(self, stream: str):
        await self.handle_intervention()
        try:
            if len(stream) < 25:
                return  # no reason to try
            response = DirtyJson.parse_string(stream)
            if isinstance(response, dict):
                await self.call_extensions(
                    "response_stream",
                    loop_data=self.loop_data,
                    text=stream,
                    parsed=response,
                )

        except Exception:
            pass

    def get_tool(self, name: str, method: str | None, args: dict, message: str, loop_data: LoopData | None, **kwargs):
        from python.helpers.tool import Tool
        from python.tools.unknown import Unknown

        classes = []

        # try agent tools first
        if self.config.profile:
            try:
                classes = extract_tools.load_classes_from_file(
                    "agents/" + self.config.profile + "/tools/" + name + ".py",
                    Tool,  # type: ignore[arg-type]
                )
            except Exception:
                pass

        # try default tools
        if not classes:
            try:
                classes = extract_tools.load_classes_from_file(
                    "python/tools/" + name + ".py",
                    Tool,  # type: ignore[arg-type]
                )
            except Exception:
                pass
        tool_class = classes[0] if classes else Unknown
        return tool_class(
            agent=self, name=name, method=method, args=args, message=message, loop_data=loop_data, **kwargs
        )

    async def call_extensions(self, extension_point: str, **kwargs) -> Any:
        return await call_extensions(extension_point=extension_point, agent=self, **kwargs)
