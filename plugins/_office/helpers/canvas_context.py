from __future__ import annotations

from typing import Any

from plugins._desktop.helpers import desktop_state
from plugins._office.helpers import document_store


def build_context(max_items: int = 6) -> str:
    documents = document_store.get_open_documents(limit=max_items)
    desktop_context = build_desktop_context()
    if not documents:
        return desktop_context

    lines = [
        "These document artifacts have active document sessions. Content is omitted; load skill `document-artifacts` for edit workflow, then use `document_artifact` with action `read` before content-sensitive edits.",
    ]
    for doc in documents:
        lines.append(format_document_line(doc))
    lines.append(
        "Use `document_artifact` with action `edit` and file_id or path for saved edits; tool results refresh the document canvas."
    )
    if desktop_context:
        lines.extend(["", desktop_context])
    return "\n".join(lines)


def format_document_line(doc: dict[str, Any]) -> str:
    return (
        f"- {doc.get('basename', 'Untitled')} "
        f"(.{doc.get('extension', '')}, file_id={doc.get('file_id', '')}, "
        f"path={document_store.display_path(doc.get('path', ''))}, version={document_store.item_version(doc)}, "
        f"size={doc.get('size', 0)} bytes, last_modified={doc.get('last_modified', '')}, "
        f"open_sessions={doc.get('open_sessions', 1)})"
    )


def build_desktop_context() -> str:
    if not desktop_state.session_manifest_exists():
        return ""
    try:
        return desktop_state.compact_prompt_context(
            desktop_state.collect_state(include_screenshot=False),
        )
    except Exception as exc:
        return (
            "[DESKTOP STATE]\n"
            f"- unavailable={exc}\n"
            "- next=Open the Desktop surface manually, then run plugins/_desktop/skills/linux-desktop/scripts/desktopctl.sh observe --json."
        )
