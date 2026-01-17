from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files
from instruments.custom.knowledge_ingest.knowledge_ingest_db import KnowledgeIngestDatabase


class TelegramInboxList(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        limit = int(input.get("limit", 50))
        since_hours = int(input.get("since_hours", 72))

        db_path = files.get_abs_path("./instruments/custom/knowledge_ingest/data/knowledge_ingest.db")
        db = KnowledgeIngestDatabase(db_path)
        items = db.list_items(since_hours=since_hours, tags=["telegram"], limit=limit)

        results = []
        for item in items:
            chat_id = ""
            for tag in item.get("tags", []):
                if tag.startswith("chat:"):
                    chat_id = tag.split(":", 1)[1]
                    break
            results.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "content": item.get("content"),
                    "tags": item.get("tags"),
                    "chat_id": chat_id,
                    "created_at": item.get("created_at"),
                }
            )

        return {"items": results}
