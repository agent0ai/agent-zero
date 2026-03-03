from python.helpers.api import ApiHandler, Input, Output, Request, Response

from python.helpers import persist_chat
from python.helpers.audit_log import extract_urls, log_event
from python.helpers.review_gate import get_gate

class ExportChat(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")

        context = self.use_context(ctxid)

        gate = get_gate(context)
        if gate and gate.get("status") in {"required", "failed", "stale"}:
            status = gate.get("status", "required")
            return Response(
                response=(
                    "Export blocked: review not completed.\n"
                    f"review_status={status}\n"
                    "Run a LegalFlow review and ensure it passes before exporting."
                ),
                status=409,
                mimetype="text/plain",
            )

        content = persist_chat.export_json_chat(context)

        try:
            sources = extract_urls(content)[:50]
            file_paths = [f"{persist_chat.CHATS_FOLDER}/{context.id}/{persist_chat.CHAT_FILE_NAME}"]
            log_event(
                agent_role="api",
                user_action="api:/chat_export",
                sources=sources,
                output=content,
                file_paths_touched=file_paths,
                extra={"ctxid": context.id, "content_len": len(content)},
            )
        except Exception:
            # Audit logging must never break the API flow.
            pass

        return {
            "message": "Chats exported.",
            "ctxid": context.id,
            "content": content,
        }
