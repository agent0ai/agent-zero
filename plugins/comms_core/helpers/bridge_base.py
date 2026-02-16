"""
Communication Bridge base class.

Provides the shared abstraction that all channel plugins build on.
Platform subclasses implement transport (receiving events, sending messages,
downloading attachments). This base handles chat mapping, agent context
management, command handling, and timeout protection.

Agent interaction uses direct AgentContext.communicate() calls rather
than HTTP loopback.
"""

import asyncio
import logging
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from plugins.comms_core.helpers.chat_mapping import ChatMapping


@dataclass
class NormalisedAttachment:
    """Platform-agnostic attachment representation."""

    filename: str
    content_bytes: bytes
    mime_type: str

    def save_to_disk(self, upload_dir: str) -> str:
        """Save attachment to disk and return the file path."""
        os.makedirs(upload_dir, exist_ok=True)
        # Sanitize filename to prevent path traversal
        safe_filename = os.path.basename(self.filename)
        if not safe_filename or safe_filename in (".", ".."):
            safe_filename = "attachment"
        path = os.path.join(upload_dir, safe_filename)
        with open(path, "wb") as f:
            f.write(self.content_bytes)
        return path


@dataclass
class InboundMessage:
    """Platform-agnostic inbound message."""

    platform: str  # "telegram", "slack", "discord"
    platform_chat_id: str  # Platform's chat/channel identifier
    platform_user_id: str  # Platform's user identifier
    platform_message_id: str  # For threading/replies
    text: str  # Message text (or transcription for voice)
    attachments: list[NormalisedAttachment] = field(default_factory=list)
    is_voice: bool = False  # Was this a voice note?
    voice_audio_bytes: bytes | None = None  # Raw audio for STT
    raw_event: Any = None  # Platform-specific event object


@dataclass
class OutboundMessage:
    """Platform-agnostic outbound message."""

    platform_chat_id: str
    text: str
    voice_audio_bytes: bytes | None = None
    reply_to_message_id: str | None = None


@dataclass
class BridgeConfig:
    """Configuration resolved from env vars and plugin settings."""

    default_project: str = ""
    context_lifetime_hours: int = 24
    voice_reply_mode: str = "text"  # "text", "voice", "both"
    allowed_users: set[str] = field(default_factory=set)  # Empty = allow all
    message_timeout: int = 300  # Seconds before agent response times out


class CommunicationBridge(ABC):
    """
    Abstract base for all communication channel bridges.

    Subclasses implement platform-specific transport (receiving events,
    sending messages, downloading attachments). The base class handles
    chat mapping, agent context management, command handling,
    and timeout protection.
    """

    def __init__(self, config: BridgeConfig, logger: logging.Logger | None = None):
        self.config = config
        self.logger = logger or logging.getLogger(f"a0.comms.{self.platform_name}")
        self._chat_map = ChatMapping(self.platform_name)
        self._running = False
        self._task: asyncio.Task | None = None

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return platform identifier: 'telegram', 'slack', 'discord'."""
        ...

    @abstractmethod
    async def start_transport(self) -> None:
        """Start the platform SDK (polling loop, socket mode, gateway)."""
        ...

    @abstractmethod
    async def stop_transport(self) -> None:
        """Gracefully shut down the platform SDK."""
        ...

    @abstractmethod
    async def send_text(
        self, chat_id: str, text: str, reply_to: str | None = None
    ) -> None:
        """Send a text message via platform SDK."""
        ...

    @abstractmethod
    async def send_voice(
        self, chat_id: str, audio_bytes: bytes, reply_to: str | None = None
    ) -> None:
        """Send a voice note/audio message via platform SDK."""
        ...

    @abstractmethod
    async def send_typing_indicator(
        self, chat_id: str, action: str = "typing"
    ) -> None:
        """Send a typing/recording indicator to the platform."""
        ...

    @abstractmethod
    async def download_attachment(
        self, platform_file_ref: Any
    ) -> NormalisedAttachment:
        """Download a file from the platform and normalise it."""
        ...

    # --- Concrete methods (shared across all platforms) ---

    async def start(self) -> None:
        """Start the bridge. Called from agent_init extension."""
        if self._running:
            self.logger.warning(f"{self.platform_name} bridge already running")
            return
        await self._chat_map.load()
        self._running = True
        self.logger.info(f"{self.platform_name} bridge starting")
        await self.start_transport()

    async def stop(self) -> None:
        """Stop the bridge. Called on shutdown."""
        self._running = False
        await self.stop_transport()
        await self._chat_map.save()
        self.logger.info(f"{self.platform_name} bridge stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def active_chats(self) -> int:
        return len(self._chat_map)

    async def handle_inbound(self, message: InboundMessage) -> None:
        """
        Core inbound message handler. Platform subclasses call this
        after normalising the platform event into an InboundMessage.
        """
        # Access control
        if (
            self.config.allowed_users
            and message.platform_user_id not in self.config.allowed_users
        ):
            self.logger.warning(
                f"Rejected message from unauthorised user: {message.platform_user_id}"
            )
            return

        if not message.text.strip():
            return

        # Resolve context
        context_id = self._chat_map.get_context_id(message.platform_chat_id)

        # Handle commands
        if message.text.startswith("/"):
            handled = await self._handle_command(message, context_id)
            if handled:
                return

        # Send typing indicator
        await self.send_typing_indicator(message.platform_chat_id, "typing")

        # Call agent directly via AgentContext.communicate()
        try:
            response_text = await self._communicate_with_agent(
                message, context_id, "typing"
            )
        except asyncio.TimeoutError:
            self.logger.warning(
                f"Agent response timed out after {self.config.message_timeout}s "
                f"for chat {message.platform_chat_id}"
            )
            await self.send_text(
                message.platform_chat_id,
                "Request timed out. The agent took too long to respond. "
                "Please try again with a simpler request.",
            )
            return
        except Exception as e:
            self.logger.error(f"Agent communication failed: {e}", exc_info=True)
            await self.send_text(
                message.platform_chat_id,
                "Sorry, something went wrong processing your message. "
                "Please try again.",
            )
            return

        if not response_text:
            return

        await self.send_text(
            message.platform_chat_id,
            response_text,
            reply_to=message.platform_message_id,
        )

    async def _communicate_with_agent(
        self,
        message: InboundMessage,
        context_id: str | None,
        typing_action: str,
    ) -> str:
        """
        Create or retrieve an AgentContext and call communicate().

        Wraps the call in asyncio.wait_for() with the configured timeout.
        Refreshes typing indicators periodically during long operations.

        Returns:
            Agent response text.

        Raises:
            asyncio.TimeoutError: If agent doesn't respond within timeout.
        """
        # Lazy imports to avoid circular dependencies at module level
        from agent import AgentContext, UserMessage
        from initialize import initialize_agent
        from python.helpers import files

        # Get or create context
        agent_context: AgentContext | None = None
        if context_id:
            agent_context = AgentContext.get(context_id)

        if agent_context is None:
            # Create new context with current agent config
            config = initialize_agent()
            agent_context = AgentContext(config=config)
            context_id = agent_context.id

        # Update chat mapping with current context
        self._chat_map.set(
            message.platform_chat_id,
            context_id,
            platform_user_id=message.platform_user_id,
        )

        # Save attachments to disk (A0 expects file paths, not base64)
        attachment_paths: list[str] = []
        if message.attachments:
            upload_dir = files.get_abs_path("usr/uploads")
            for att in message.attachments:
                path = att.save_to_disk(upload_dir)
                attachment_paths.append(path)

        # Build user message
        user_msg = UserMessage(
            message=message.text,
            attachments=attachment_paths,
        )

        # Run agent with timeout and periodic typing refresh.
        # DeferredTask.result() blocks until completion, so we poll
        # is_ready() and refresh typing indicators every ~4 seconds.
        async def _run_with_typing() -> str:
            task = agent_context.communicate(user_msg)

            while not task.is_ready():
                await asyncio.sleep(4.0)
                if not task.is_ready():
                    try:
                        await self.send_typing_indicator(
                            message.platform_chat_id, typing_action
                        )
                    except Exception:
                        pass

            return await task.result() or ""

        return await asyncio.wait_for(
            _run_with_typing(),
            timeout=self.config.message_timeout,
        )

    async def handle_outbound(self, outbound: OutboundMessage) -> None:
        """Send an outbound message. Called from the channel_send tool."""
        if outbound.voice_audio_bytes:
            await self.send_voice(
                outbound.platform_chat_id,
                outbound.voice_audio_bytes,
                reply_to=outbound.reply_to_message_id,
            )
        else:
            await self.send_text(
                outbound.platform_chat_id,
                outbound.text,
                reply_to=outbound.reply_to_message_id,
            )

    async def _handle_command(
        self, message: InboundMessage, context_id: str | None
    ) -> bool:
        """Handle slash commands. Returns True if the command was handled."""
        cmd = message.text.strip().split()[0].lower()

        if cmd in ("/start", "/help"):
            await self.send_text(
                message.platform_chat_id,
                f"Agent Zero is connected via {self.platform_name}.\n\n"
                "Commands:\n"
                "/reset - Start a new conversation\n"
                "/status - Show bridge and context status\n"
                "/id - Show your platform user ID",
            )
            return True

        if cmd == "/reset":
            self._chat_map.remove(message.platform_chat_id)
            await self.send_text(message.platform_chat_id, "Conversation reset.")
            return True

        if cmd == "/status":
            ctx = f"Context: {context_id}" if context_id else "No active context"
            chats = self.active_chats
            await self.send_text(
                message.platform_chat_id,
                f"Bridge: {'running' if self._running else 'stopped'}\n"
                f"Platform: {self.platform_name}\n"
                f"{ctx}\n"
                f"Active chats: {chats}\n"
                f"Timeout: {self.config.message_timeout}s",
            )
            return True

        if cmd == "/id":
            await self.send_text(
                message.platform_chat_id,
                f"Your user ID: {message.platform_user_id}\n"
                f"Chat ID: {message.platform_chat_id}",
            )
            return True

        return False  # Not a recognised command, pass through to agent
