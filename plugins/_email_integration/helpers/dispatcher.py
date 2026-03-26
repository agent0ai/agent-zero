"""
Email dispatch logic — routes inbound emails to chats. 

No agent deps in pure helpers.
"""

import re
from dataclasses import dataclass
from typing import Literal, TypedDict

# Pattern for extracting chat thread ID from email subject
# Matches: [a0-xxxxxxxx] at end of subject
_THREAD_ID_RE = re.compile(r"\[a0-([a-zA-Z0-9]+)\]")

# Context data keys (no underscore prefix — must persist across restarts)
CTX_EMAIL_HANDLER = "email_handler"
CTX_EMAIL_SENDER = "email_sender"
CTX_EMAIL_THREAD_ID = "email_thread_id"
CTX_EMAIL_SUBJECT = "email_subject"
CTX_EMAIL_MESSAGE_ID = "email_message_id"
CTX_EMAIL_REFERENCES = "email_references"
CTX_EMAIL_LAST_BODY = "email_last_body"
# Transient — consumed per-reply, not persisted
CTX_EMAIL_ATTACHMENTS = "_email_response_attachments"

BODY_PREVIEW_MAX_CHARS: int = 2000

DispatchAction = Literal["new_chat", "continue_chat"]


@dataclass
class DispatchDecision:
    action: DispatchAction
    context_id: str = ""
    reason: str = ""


def extract_thread_id(subject: str) -> str:
    match = _THREAD_ID_RE.search(subject)
    return match.group(1) if match else ""


def build_reply_subject(original_subject: str, thread_id: str) -> str:
    clean = _THREAD_ID_RE.sub("", original_subject).strip()
    if not clean.lower().startswith("re:"):
        clean = f"Re: {clean}"
    return f"{clean} [a0-{thread_id}]"


class ChatSummary(TypedDict):
    context_id: str
    thread_id: str
    sender: str
    subject: str
    handler: str
    history_preview: str


def build_chat_summary(context_id: str, data: dict) -> ChatSummary:
    return {
        "context_id": context_id,
        "thread_id": data.get(CTX_EMAIL_THREAD_ID, ""),
        "sender": data.get(CTX_EMAIL_SENDER, ""),
        "subject": data.get(CTX_EMAIL_SUBJECT, ""),
        "handler": data.get(CTX_EMAIL_HANDLER, ""),
        "history_preview": "",
    }


# ------------------------------------------------------------------
# Dispatcher prompt builders
# ------------------------------------------------------------------

def truncate_body(body: str) -> str:
    if len(body) <= BODY_PREVIEW_MAX_CHARS:
        return body
    return body[:BODY_PREVIEW_MAX_CHARS] + "... (truncated)"


def format_chats_list(existing_chats: list[ChatSummary]) -> str:
    if not existing_chats:
        return "No existing chats for this handler."
    sections = []
    for c in existing_chats[:20]:
        header = (
            f"- context_id={c['context_id']}"
            f" sender={c.get('sender', '')} subject={c.get('subject', '')}"
        )
        preview = c.get("history_preview", "")
        if preview:
            header += f"\n  conversation:\n  {preview}"
        sections.append(header)
    return "\n".join(sections)


def parse_dispatcher_response(response: str) -> DispatchDecision:
    line = response.strip().split("\n")[0].strip()
    parts = line.split(None, 2)

    if len(parts) < 2:
        return DispatchDecision(action="new_chat", reason="unparseable response")

    action_raw = parts[0].upper()
    ctx_id = parts[1] if parts[1] != "_" else ""
    reason = parts[2] if len(parts) > 2 else ""

    action_map: dict[str, DispatchAction] = {
        "NEW_CHAT": "new_chat",
        "CONTINUE": "continue_chat",
    }
    action = action_map.get(action_raw, "new_chat")
    return DispatchDecision(action=action, context_id=ctx_id, reason=reason)
