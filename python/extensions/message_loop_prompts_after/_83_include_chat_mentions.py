from python.helpers.extension import Extension
from python.helpers.print_style import PrintStyle
from agent import AgentContext, LoopData

MAX_CHAT_CHARS = 10000
FIRST_MESSAGES = 5
LAST_MESSAGES = 10


class IncludeChatMentions(Extension):
    """Inject @mentioned chat history into agent prompts."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        mentions = self.agent.data.get("mentions", [])
        chat_mentions = [m for m in mentions if m.get("type") == "chat"]
        if not chat_mentions:
            return

        current_ctx_id = self.agent.context.id if self.agent.context else None

        for mention in chat_mentions:
            context_id = mention.get("context_id", "")
            if not context_id or context_id == current_ctx_id:
                continue

            try:
                messages_text = self._extract_chat_history(context_id)
            except Exception as e:
                PrintStyle.error(f"[chat_mentions] Error extracting history for {context_id}: {e}")
                continue

            if not messages_text:
                PrintStyle(font_color="yellow", padding=False).print(
                    f"[chat_mentions] No messages found in context {context_id}"
                )
                continue

            title = mention.get("title", "Previous chat")
            context = self.agent.read_prompt(
                "agent.extras.chat_mention.md",
                title=title,
                context_id=context_id,
                messages=messages_text,
            )

            if context:
                key = f"chat_mention_{context_id}"
                loop_data.extras_temporary[key] = context
                PrintStyle(font_color="green", padding=False).print(
                    f"[chat_mentions] Injected {len(messages_text)} chars from '{title}'"
                )

    def _extract_chat_history(self, context_id: str) -> str:
        """Load chat log and apply smart truncation (first N + last M messages)."""
        ctx = AgentContext.get(context_id)
        if not ctx:
            PrintStyle(font_color="yellow", padding=False).print(
                f"[chat_mentions] Context {context_id} not in memory, trying disk..."
            )
            ctx = self._load_context_from_disk(context_id)
        if not ctx:
            PrintStyle(font_color="yellow", padding=False).print(
                f"[chat_mentions] Context {context_id} not found anywhere"
            )
            return ""

        # Get all log items
        all_items = ctx.log.output(start=0)
        if not all_items:
            PrintStyle(font_color="yellow", padding=False).print(
                f"[chat_mentions] Context {context_id} has empty log"
            )
            return ""

        # Filter to user and response messages only
        conversation = [
            item for item in all_items
            if item.get("type") in ("user", "response")
            and item.get("content")
        ]

        if not conversation:
            # Log the types we found for debugging
            types_found = set(item.get("type", "?") for item in all_items)
            PrintStyle(font_color="yellow", padding=False).print(
                f"[chat_mentions] Context {context_id} has {len(all_items)} log items but no user/response. Types: {types_found}"
            )
            return ""

        # Apply smart truncation: first N + last M
        total = len(conversation)
        if total <= FIRST_MESSAGES + LAST_MESSAGES:
            selected = conversation
            omitted = 0
        else:
            first = conversation[:FIRST_MESSAGES]
            last = conversation[-LAST_MESSAGES:]
            omitted = total - FIRST_MESSAGES - LAST_MESSAGES
            selected = first + [None] + last  # None = separator

        # Format messages
        lines = []
        for item in selected:
            if item is None:
                lines.append(f"\n... ({omitted} messages omitted) ...\n")
                continue

            msg_type = item.get("type", "")
            content = item.get("content", "")

            # Content can be a dict (from template rendering) or string
            if isinstance(content, dict):
                content = content.get("content", str(content))

            role = "User" if msg_type == "user" else "Agent"
            lines.append(f"**{role}:** {content}")

        result = "\n\n".join(lines)

        # Enforce total character limit
        if len(result) > MAX_CHAT_CHARS:
            result = result[:MAX_CHAT_CHARS] + "\n\n... (truncated)"

        return result

    def _load_context_from_disk(self, context_id: str) -> "AgentContext | None":
        """Attempt to load a context from persisted chat files."""
        try:
            from python.helpers import persist_chat, files
            import json

            chat_file = files.get_abs_path(persist_chat.CHATS_FOLDER, context_id, persist_chat.CHAT_FILE_NAME)
            if not files.exists(chat_file):
                return None

            js = files.read_file(chat_file)
            data = json.loads(js)
            # Only deserialize the log — we just need the conversation history
            log_data = data.get("log")
            if not log_data:
                return None

            log = persist_chat._deserialize_log(log_data)

            # Check if deserialization registered the context as a side-effect
            ctx = AgentContext.get(context_id)
            if ctx:
                return ctx  # It was loaded by deserialization side-effect

            # Build a lightweight read-only context
            class _LogProxy:
                """Minimal proxy for reading chat history without full context."""
                def __init__(self, ctx_id, ctx_log):
                    self.id = ctx_id
                    self.log = ctx_log
            return _LogProxy(context_id, log)
        except Exception as e:
            PrintStyle.error(f"[chat_mentions] Failed to load context {context_id} from disk: {e}")
            return None
