import os
import uuid
from typing import TYPE_CHECKING
from python.helpers import guids

if TYPE_CHECKING:
    from agent import AgentContext

from python.helpers.print_style import PrintStyle

QUEUE_KEY = "message_queue"
QUEUE_SEQ_KEY = "message_queue_seq"
UPLOAD_FOLDER = "/a0/usr/uploads"


def get_queue(context: "AgentContext") -> list:
    """Get current queue from context.data."""
    return context.get_data(QUEUE_KEY) or []


def _get_next_seq(context: "AgentContext") -> int:
    """Get next sequence number."""
    seq = context.get_data(QUEUE_SEQ_KEY) or 0
    seq += 1
    context.set_data(QUEUE_SEQ_KEY, seq)
    return seq


def _sync_output(context: "AgentContext"):
    """Sync queue to output_data for frontend polling."""
    queue = get_queue(context)
    # Truncate text for frontend display
    truncated = []
    for item in queue:
        truncated.append({
            "id": item["id"],
            "seq": item.get("seq", 0),
            "text": item["text"][:100] + "..." if len(item["text"]) > 100 else item["text"],
            "attachments": [a.split("/")[-1] for a in item.get("attachments", [])],
            "attachment_count": len(item.get("attachments", [])),
        })
    context.set_output_data(QUEUE_KEY, truncated)


def add(
    context: "AgentContext",
    text: str,
    attachments: list[str] | None = None,
    item_id: str | None = None,
) -> dict:
    """Add message to queue. Attachments should be filenames, will be converted to full paths."""
    queue = get_queue(context)
    
    # Convert filenames to full paths
    full_paths = []
    for att in (attachments or []):
        if att.startswith("/"):
            full_paths.append(att)
        else:
            full_paths.append(f"{UPLOAD_FOLDER}/{att}")
    
    item = {
        "id": item_id or guids.generate_id(),
        "seq": _get_next_seq(context),
        "text": text,
        "attachments": full_paths,
    }
    queue.append(item)
    context.set_data(QUEUE_KEY, queue)
    _sync_output(context)
    return item


def remove(context: "AgentContext", item_id: str | None = None) -> int:
    """Remove item(s). If item_id is None, clears all. Returns remaining count."""
    if not item_id:
        context.set_data(QUEUE_KEY, [])
        context.set_output_data(QUEUE_KEY, [])
        return 0
    queue = [i for i in get_queue(context) if i["id"] != item_id]
    context.set_data(QUEUE_KEY, queue)
    _sync_output(context)
    return len(queue)


def pop_first(context: "AgentContext") -> dict | None:
    """Remove and return first item."""
    queue = get_queue(context)
    if not queue:
        return None
    item = queue.pop(0)
    context.set_data(QUEUE_KEY, queue)
    _sync_output(context)
    return item


def pop_item(context: "AgentContext", item_id: str) -> dict | None:
    """Remove and return specific item."""
    queue = get_queue(context)
    for i, item in enumerate(queue):
        if item["id"] == item_id:
            queue.pop(i)
            context.set_data(QUEUE_KEY, queue)
            _sync_output(context)
            return item
    return None


def has_queue(context: "AgentContext") -> bool:
    """Check if queue has items."""
    return len(get_queue(context)) > 0


def log_user_message(
    context: "AgentContext",
    message: str,
    attachment_paths: list[str],
    message_id: str | None = None,
    source: str = "",
):
    """Log user message to console and UI. Used by message API and queue processing."""
    # Prepare attachment filenames for logging
    attachment_filenames = (
        [os.path.basename(path) for path in attachment_paths]
        if attachment_paths
        else []
    )
    
    # Print to console
    label = f"User message{source}:"
    PrintStyle(
        background_color="#6C3483", font_color="white", bold=True, padding=True
    ).print(label)
    PrintStyle(font_color="white", padding=False).print(f"> {message}")
    if attachment_filenames:
        PrintStyle(font_color="white", padding=False).print("Attachments:")
        for filename in attachment_filenames:
            PrintStyle(font_color="white", padding=False).print(f"- {filename}")
    
    # Log to UI
    context.log.log(
        type="user",
        heading="",
        content=message,
        kvps={"attachments": attachment_filenames},
        id=message_id,
    )


def send_message(context: "AgentContext", item: dict, source: str = " (from queue)"):
    """Send a single queued message (log + communicate)."""
    from agent import UserMessage  # Import here to avoid circular import
    
    message = item.get("text", "")
    attachments = item.get("attachments", [])
    log_user_message(context, message, attachments, source=source)
    context.communicate(UserMessage(message, attachments))


def send_next(context: "AgentContext") -> bool:
    """Send next queued message. Returns True if sent, False if queue empty."""
    if not has_queue(context):
        return False
    item = pop_first(context)
    if item:
        send_message(context, item)
        return True
    return False


def send_all_aggregated(context: "AgentContext") -> int:
    """Aggregate and send all queued messages as one. Returns count of items sent."""
    from agent import UserMessage  # Import here to avoid circular import
    
    if not has_queue(context):
        return 0
    
    items = []
    while has_queue(context):
        items.append(pop_first(context))
    
    # Combine texts with separator
    text = "\n\n---\n\n".join(i["text"] for i in items if i["text"])
    attachments = [a for i in items for a in i.get("attachments", [])]
    
    log_user_message(context, text, attachments, source=" (queued batch)")
    context.communicate(UserMessage(text, attachments))
    return len(items)
