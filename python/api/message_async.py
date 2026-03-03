from agent import AgentContext
from python.helpers.defer import DeferredTask
from python.api.message import Message
from python.helpers.audit_log import log_message_async_intake


class MessageAsync(Message):
    async def process(self, input: dict, request):  # type: ignore[override]
        content_type = request.content_type or ""
        if content_type.startswith("multipart/form-data"):
            text = request.form.get("text", "")
            ctxid = request.form.get("context", "")
            message_id = request.form.get("message_id", None)
            attachments = request.files.getlist("attachments")
            attachment_filenames = [
                a.filename for a in attachments if getattr(a, "filename", None)
            ]
        else:
            input_data = request.get_json(silent=True) or {}
            text = input_data.get("text", "") or ""
            ctxid = input_data.get("context", "") or ""
            message_id = input_data.get("message_id", None)
            attachment_filenames = []

        try:
            log_message_async_intake(
                request_path=getattr(request, "path", "/message_async"),
                content_type=content_type,
                text=text,
                context_id=ctxid,
                message_id=message_id,
                attachment_filenames=attachment_filenames,
            )
        except Exception:
            # Audit logging must never break the API flow.
            pass

        return await super().process(input=input, request=request)

    async def respond(self, task: DeferredTask, context: AgentContext):
        return {
            "message": "Message received.",
            "context": context.id,
        }
