import os
import uuid

from agent import AgentContext, UserMessage
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.print_style import PrintStyle
from python.helpers import extension
from python.helpers.telegram_bridge import (
    get_context_for_chat,
    set_context_for_chat,
    should_ignore_update,
    clear_context_for_chat,
    extract_tags,
    build_title,
)
from python.helpers.telegram_client import send_message


class TelegramWebhook(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request):
        secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
        if secret:
            header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if header != secret:
                return Response(response="forbidden", status=403, mimetype="text/plain")

        data = request.get_json(silent=True) or {}
        update_id = data.get("update_id")
        message = data.get("message") or data.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text = message.get("text") or message.get("caption")

        if not chat_id or not text:
            return {"status": "ignored"}

        chat_id_str = str(chat_id)
        if isinstance(update_id, int) and should_ignore_update(chat_id_str, update_id):
            return {"status": "duplicate"}

        if text.strip().lower() in {"/new", "/reset"}:
            clear_context_for_chat(chat_id_str)
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            if token:
                send_message(token, chat_id_str, "Context reset. Start a new thread.")
            return {"status": "reset"}

        shared_context = os.getenv("TELEGRAM_AGENT_CONTEXT")
        ctxid = shared_context or get_context_for_chat(chat_id_str)
        if not ctxid:
            ctxid = f"telegram-{uuid.uuid4().hex}"
        if not shared_context:
            set_context_for_chat(chat_id_str, ctxid)

        context = self.use_context(ctxid)

        data = {"message": text, "attachment_paths": []}
        await extension.call_extensions("user_message_ui", agent=context.get_agent(), data=data)
        text = data.get("message", "")

        tags = extract_tags(text)
        tags.append(f"chat:{chat_id_str}")
        tags = sorted(set(tags))
        title = build_title(text)

        PrintStyle(font_color="white", padding=True).print(f"[Telegram] {chat_id_str}: {text}")

        await self._store_telegram_message(text, title, tags)

        task = context.communicate(UserMessage(text, []))
        result = await task.result()  # type: ignore

        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token:
            send_message(token, chat_id_str, result)

        return {"status": "ok"}

    async def _store_telegram_message(self, text: str, title: str, tags: list[str]) -> None:
        try:
            from python.helpers import files
            from instruments.custom.knowledge_ingest.knowledge_ingest_db import KnowledgeIngestDatabase
            from instruments.custom.knowledge_ingest.knowledge_ingest_manager import KnowledgeIngestManager

            db_path = files.get_abs_path(
                "./instruments/custom/knowledge_ingest/data/knowledge_ingest.db"
            )
            db = KnowledgeIngestDatabase(db_path)
            source_name = "Telegram Inbox"
            source_uri = "telegram://inbox"
            source_id = db.find_source(source_name, source_uri)
            if not source_id:
                source_id = db.add_source(
                    name=source_name,
                    source_type="telegram",
                    uri=source_uri,
                    tags=["telegram"],
                    cadence="daily",
                    config={},
                )

            source = db.get_source(source_id)
            if not source:
                return

            manager = KnowledgeIngestManager(db_path)
            item = {
                "title": title,
                "url": None,
                "published_at": None,
                "content": text,
                "tags": tags,
                "confidence": 0.8,
            }
            manager.store_external_items(source, [item])
        except Exception as exc:
            PrintStyle.error(f"Telegram ingestion failed: {exc}")
