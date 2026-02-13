"""AG-UI Protocol server implementation for Agent Zero.

This module provides the core AG-UI adapter that bridges Agent Zero's
message loop with the AG-UI SSE streaming protocol.
"""

import asyncio
import uuid
from typing import Any, AsyncGenerator
from dataclasses import dataclass, field

from python.helpers.print_style import PrintStyle
from python.helpers import settings, projects
from python.helpers.persist_chat import remove_chat
from python.helpers.agui_validation import RunAgentInput, extract_user_message

# Import AG-UI SDK components
try:
    from ag_ui.core import (
        # Run lifecycle events
        RunStartedEvent,
        RunFinishedEvent,
        RunErrorEvent,
        # Text message events
        TextMessageStartEvent,
        TextMessageContentEvent,
        TextMessageEndEvent,
        # Tool call events
        ToolCallStartEvent,
        ToolCallArgsEvent,
        ToolCallEndEvent,
        ToolCallResultEvent,
        # State management events
        StateSnapshotEvent,
        StateDeltaEvent,
        # Messages snapshot
        MessagesSnapshotEvent,
        # Step events
        StepStartedEvent,
        StepFinishedEvent,
        # Extensibility events
        CustomEvent,
        RawEvent,
        # Base and enums
        BaseEvent,
        EventType,
        Message,
        Role,
    )
    from ag_ui.encoder import EventEncoder

    AGUI_AVAILABLE = True

    # Check if thinking events are available (may be in newer SDK versions)
    try:
        from ag_ui.core import (
            ThinkingStartEvent,
            ThinkingEndEvent,
            ThinkingTextMessageStartEvent,
            ThinkingTextMessageContentEvent,
            ThinkingTextMessageEndEvent,
        )
        THINKING_EVENTS_AVAILABLE = True
    except ImportError:
        THINKING_EVENTS_AVAILABLE = False

except ImportError:
    AGUI_AVAILABLE = False
    THINKING_EVENTS_AVAILABLE = False

    # Stub classes for type checking when AG-UI is not installed
    class BaseEvent:  # type: ignore
        pass

    class EventEncoder:  # type: ignore
        def encode(self, event: Any) -> str:
            return ""

        def get_content_type(self) -> str:
            return "text/event-stream"


_PRINTER = PrintStyle(italic=True, font_color="cyan", padding=False)


# Fallback event classes for thinking (if not in SDK version)
if not THINKING_EVENTS_AVAILABLE:
    @dataclass
    class ThinkingStartEvent:
        """Emitted when thinking/reasoning begins."""
        type: str = "THINKING_START"

    @dataclass
    class ThinkingEndEvent:
        """Emitted when thinking/reasoning ends."""
        type: str = "THINKING_END"

    @dataclass
    class ThinkingTextMessageStartEvent:
        """Start of a thinking text message."""
        message_id: str
        type: str = "THINKING_TEXT_MESSAGE_START"

    @dataclass
    class ThinkingTextMessageContentEvent:
        """Thinking text content chunk."""
        message_id: str
        delta: str
        type: str = "THINKING_TEXT_MESSAGE_CONTENT"

    @dataclass
    class ThinkingTextMessageEndEvent:
        """End of a thinking text message."""
        message_id: str
        type: str = "THINKING_TEXT_MESSAGE_END"


# Export event classes for extensions to use
__all__ = [
    # Core classes
    "AguiServer",
    "AguiRunData",
    # Availability flags
    "AGUI_AVAILABLE",
    "THINKING_EVENTS_AVAILABLE",
    # Server functions
    "is_available",
    "get_server",
    "get_run_data",
    # Event emission helpers
    "emit_custom_event",
    "emit_raw_event",
    "emit_state_delta",
    # Thinking event classes (use SDK when available, fallback otherwise)
    "ThinkingStartEvent",
    "ThinkingEndEvent",
    "ThinkingTextMessageStartEvent",
    "ThinkingTextMessageContentEvent",
    "ThinkingTextMessageEndEvent",
]


@dataclass
class AguiRunData:
    """Data associated with an active AG-UI run."""
    thread_id: str
    run_id: str
    message_id: str
    context_id: str
    queue: asyncio.Queue
    # Text message tracking
    text_started: bool = False
    # Thinking tracking
    thinking_started: bool = False
    thinking_message_id: str | None = None
    # Tool tracking
    current_tool_call_id: str | None = None
    # Step tracking
    current_step_id: str | None = None
    step_counter: int = 0
    # State tracking
    state: dict[str, Any] = field(default_factory=dict)
    # Activity tracking
    activities: list[dict[str, Any]] = field(default_factory=list)
    # Messages for snapshot
    messages: list[dict[str, Any]] = field(default_factory=list)


class AguiServer:
    """AG-UI Protocol server for Agent Zero.

    Manages concurrent runs and provides SSE event streaming.
    """

    _instance: "AguiServer | None" = None
    _semaphore: asyncio.Semaphore | None = None
    _active_runs: dict[tuple[str, str], AguiRunData] = {}
    _active_runs_lock: asyncio.Lock | None = None

    # Configuration
    MAX_CONCURRENT_RUNS = 50
    INACTIVITY_TIMEOUT = 5.0  # seconds - how long to wait for queue events before checking agent status

    def __init__(self):
        self._encoder = EventEncoder() if AGUI_AVAILABLE else None

    @classmethod
    def get_instance(cls) -> "AguiServer":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = AguiServer()
        return cls._instance

    @classmethod
    async def _get_semaphore(cls) -> asyncio.Semaphore:
        """Get or create the semaphore (must be called in async context)."""
        if cls._semaphore is None:
            cls._semaphore = asyncio.Semaphore(cls.MAX_CONCURRENT_RUNS)
        return cls._semaphore

    @classmethod
    async def _get_lock(cls) -> asyncio.Lock:
        """Get or create the lock (must be called in async context)."""
        if cls._active_runs_lock is None:
            cls._active_runs_lock = asyncio.Lock()
        return cls._active_runs_lock

    def encode_event(self, event: Any) -> str:
        """Encode an event to SSE format.

        Args:
            event: An AG-UI event object

        Returns:
            SSE-formatted string
        """
        if self._encoder is None:
            # Fallback manual encoding
            import json
            if hasattr(event, "__dict__"):
                data = {}
                for k, v in event.__dict__.items():
                    # Convert snake_case to camelCase for JSON
                    if k == "message_id":
                        data["messageId"] = v
                    elif k == "thread_id":
                        data["threadId"] = v
                    elif k == "run_id":
                        data["runId"] = v
                    elif k == "tool_call_id":
                        data["toolCallId"] = v
                    elif k == "tool_call_name":
                        data["toolCallName"] = v
                    else:
                        data[k] = v
                return f"data: {json.dumps(data)}\n\n"
            return f"data: {json.dumps(event)}\n\n"

        # Use SDK encoder for standard events
        try:
            return self._encoder.encode(event)
        except Exception:
            # Fallback for custom events not in SDK
            import json
            if hasattr(event, "__dict__"):
                data = {}
                for k, v in event.__dict__.items():
                    if k == "message_id":
                        data["messageId"] = v
                    elif k == "thread_id":
                        data["threadId"] = v
                    elif k == "run_id":
                        data["runId"] = v
                    elif k == "tool_call_id":
                        data["toolCallId"] = v
                    elif k == "tool_call_name":
                        data["toolCallName"] = v
                    else:
                        data[k] = v
                return f"data: {json.dumps(data)}\n\n"
            return ""

    def get_content_type(self) -> str:
        """Get the content type for SSE responses."""
        if self._encoder:
            return self._encoder.get_content_type()
        return "text/event-stream"

    async def run_agent(
        self, input_data: RunAgentInput
    ) -> AsyncGenerator[str, None]:
        """Execute an agent run and stream AG-UI events.

        Args:
            input_data: Validated AG-UI request input

        Yields:
            SSE-formatted event strings
        """
        from agent import AgentContext, UserMessage, AgentContextType
        from initialize import initialize_agent

        thread_id = input_data.thread_id
        run_id = input_data.run_id
        run_key = (thread_id, run_id)

        # Acquire semaphore for concurrency control
        semaphore = await self._get_semaphore()
        lock = await self._get_lock()

        async with semaphore:
            # Check for duplicate run
            async with lock:
                if run_key in self._active_runs:
                    _PRINTER.print(f"[AG-UI] Duplicate run rejected: {run_id}")
                    yield self.encode_event(
                        RunErrorEvent(
                            type=EventType.RUN_ERROR,
                            message="Duplicate run ID",
                            code="DUPLICATE_RUN",
                        )
                        if AGUI_AVAILABLE
                        else {"type": "RUN_ERROR", "message": "Duplicate run ID"}
                    )
                    return

            context = None
            queue: asyncio.Queue = asyncio.Queue()
            message_id = str(uuid.uuid4())

            try:
                # Create temporary context for this run
                # If agent_name specified, use it as profile override
                override_settings = None
                if input_data.agent_name and input_data.agent_name != "default":
                    override_settings = {"agent_profile": input_data.agent_name}
                    _PRINTER.print(f"[AG-UI] Using agent profile: {input_data.agent_name}")

                cfg = initialize_agent(override_settings)
                _PRINTER.print(f"[AG-UI] Config profile after init: {cfg.profile}")
                context = AgentContext(cfg, type=AgentContextType.BACKGROUND)

                # Create run data and store it
                run_data = AguiRunData(
                    thread_id=thread_id,
                    run_id=run_id,
                    message_id=message_id,
                    context_id=context.id,
                    queue=queue,
                )

                async with lock:
                    self._active_runs[run_key] = run_data

                # Store queue in agent for extensions to access
                context.agent0.set_data("_agui_queue", queue)
                context.agent0.set_data("_agui_run_data", run_data)

                # Activate project if specified
                if input_data.project:
                    projects.activate_project(context.id, input_data.project)

                _PRINTER.print(f"[AG-UI] Starting run {run_id} in context {context.id}")

                # Emit RUN_STARTED
                if AGUI_AVAILABLE:
                    yield self.encode_event(
                        RunStartedEvent(type=EventType.RUN_STARTED, thread_id=thread_id, run_id=run_id)
                    )
                else:
                    yield self.encode_event(
                        {"type": "RUN_STARTED", "threadId": thread_id, "runId": run_id}
                    )

                # Extract user message
                user_text = extract_user_message(input_data)

                # Log user message to UI
                context.log.log(
                    type="user",
                    heading="AG-UI message",
                    content=user_text,
                    kvps={"from": "AG-UI", "thread": thread_id},
                    temp=False,
                )

                # Create user message and start agent communication
                user_message = UserMessage(message=user_text, attachments=[])
                task = context.communicate(user_message)

                # Stream events from queue while agent runs
                agent_task = asyncio.create_task(task.result())

                try:
                    while True:
                        # Wait for events or agent completion
                        try:
                            event = await asyncio.wait_for(
                                queue.get(), timeout=self.INACTIVITY_TIMEOUT
                            )

                            if event is None:
                                # Sentinel for completion
                                break

                            yield self.encode_event(event)

                        except asyncio.TimeoutError:
                            # Check if agent is still running
                            if agent_task.done():
                                break
                            # Otherwise continue waiting
                            continue

                except asyncio.CancelledError:
                    agent_task.cancel()
                    raise

                # Wait for agent to complete
                try:
                    result = await agent_task
                except Exception as e:
                    _PRINTER.print(f"[AG-UI] Agent error: {e}")
                    if AGUI_AVAILABLE:
                        yield self.encode_event(
                            RunErrorEvent(
                                type=EventType.RUN_ERROR,
                                message=str(e),
                                code="AGENT_ERROR",
                            )
                        )
                    else:
                        yield self.encode_event(
                            {
                                "type": "RUN_ERROR",
                                "threadId": thread_id,
                                "runId": run_id,
                                "message": str(e),
                            }
                        )
                    return

                # Drain any remaining events
                while not queue.empty():
                    event = queue.get_nowait()
                    if event is not None:
                        yield self.encode_event(event)

                # Close any open text message
                if run_data.text_started:
                    if AGUI_AVAILABLE:
                        yield self.encode_event(
                            TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=message_id)
                        )
                    else:
                        yield self.encode_event(
                            {"type": "TEXT_MESSAGE_END", "messageId": message_id}
                        )

                # Emit RUN_FINISHED
                if AGUI_AVAILABLE:
                    yield self.encode_event(
                        RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=thread_id, run_id=run_id)
                    )
                else:
                    yield self.encode_event(
                        {"type": "RUN_FINISHED", "threadId": thread_id, "runId": run_id}
                    )

                _PRINTER.print(f"[AG-UI] Completed run {run_id}")

            except Exception as e:
                _PRINTER.print(f"[AG-UI] Error in run {run_id}: {e}")
                import traceback
                traceback.print_exc()
                if AGUI_AVAILABLE:
                    yield self.encode_event(
                        RunErrorEvent(
                            type=EventType.RUN_ERROR,
                            message=str(e),
                            code="INTERNAL_ERROR",
                        )
                    )
                else:
                    yield self.encode_event(
                        {
                            "type": "RUN_ERROR",
                            "threadId": thread_id,
                            "runId": run_id,
                            "message": str(e),
                        }
                    )

            finally:
                # Cleanup
                async with lock:
                    self._active_runs.pop(run_key, None)

                if context:
                    # Remove queue from agent
                    context.agent0.set_data("_agui_queue", None)
                    context.agent0.set_data("_agui_run_data", None)

                    # Clean up context
                    context.reset()
                    AgentContext.remove(context.id)
                    remove_chat(context.id)
                    _PRINTER.print(f"[AG-UI] Cleaned up context {context.id}")


def is_available() -> bool:
    """Check if AG-UI SDK is available."""
    return AGUI_AVAILABLE


def get_server() -> AguiServer:
    """Get the AG-UI server instance."""
    return AguiServer.get_instance()


async def emit_custom_event(agent, name: str, value: Any) -> bool:
    """Emit a custom event from an agent.

    Args:
        agent: The agent instance
        name: Custom event name
        value: Event payload (any JSON-serializable value)

    Returns:
        True if event was emitted, False if AG-UI not active
    """
    queue = agent.get_data("_agui_queue")
    if not queue:
        return False

    try:
        if AGUI_AVAILABLE:
            event = CustomEvent(
                type=EventType.CUSTOM,
                name=name,
                value=value,
            )
        else:
            event = {
                "type": "CUSTOM",
                "name": name,
                "value": value,
            }
        await queue.put(event)
        return True
    except Exception as e:
        _PRINTER.print(f"[AG-UI] Custom event error: {e}")
        return False


async def emit_raw_event(agent, event_data: dict) -> bool:
    """Emit a raw event from an agent.

    Args:
        agent: The agent instance
        event_data: Raw event data dictionary

    Returns:
        True if event was emitted, False if AG-UI not active
    """
    queue = agent.get_data("_agui_queue")
    if not queue:
        return False

    try:
        if AGUI_AVAILABLE:
            event = RawEvent(
                type=EventType.RAW,
                event=event_data,
            )
        else:
            event = {
                "type": "RAW",
                "event": event_data,
            }
        await queue.put(event)
        return True
    except Exception as e:
        _PRINTER.print(f"[AG-UI] Raw event error: {e}")
        return False


async def emit_state_delta(agent, delta: dict) -> bool:
    """Emit a state delta event from an agent.

    Args:
        agent: The agent instance
        delta: State changes dictionary (will be converted to JSON Patch format)

    Returns:
        True if event was emitted, False if AG-UI not active
    """
    queue = agent.get_data("_agui_queue")
    run_data = agent.get_data("_agui_run_data")
    if not queue or not run_data:
        return False

    try:
        # Update run_data state
        run_data.state.update(delta)

        # Convert dict to JSON Patch operations (SDK expects list)
        delta_ops = [
            {"op": "replace", "path": f"/{key}", "value": value}
            for key, value in delta.items()
        ]

        if AGUI_AVAILABLE:
            event = StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=delta_ops,
            )
        else:
            event = {
                "type": "STATE_DELTA",
                "delta": delta_ops,
            }
        await queue.put(event)
        return True
    except Exception as e:
        _PRINTER.print(f"[AG-UI] State delta error: {e}")
        return False


def get_run_data(agent) -> AguiRunData | None:
    """Get the AG-UI run data for an agent.

    Args:
        agent: The agent instance

    Returns:
        AguiRunData if AG-UI is active, None otherwise
    """
    return agent.get_data("_agui_run_data")
