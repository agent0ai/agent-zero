from __future__ import annotations

import re
import time

from agent import AgentContext
from helpers.print_style import PrintStyle
from plugins._telegram_integration.helpers import telegram_client as tc
from plugins._telegram_integration.helpers.bot_manager import get_bot
from plugins._telegram_integration.helpers.constants import (
    CTX_TG_BOT,
    CTX_TG_CHAT_ID,
    CTX_TG_PROGRESS_LINES,
    CTX_TG_PROGRESS_MESSAGE_ID,
    CTX_TG_REPLY_TO,
    CTX_TG_RESPONSE_LAST_UPDATE,
    CTX_TG_RESPONSE_MESSAGE_ID,
    CTX_TG_RESPONSE_TEXT,
    CTX_TG_STREAM_ENABLED,
    CTX_TG_TOOLS_ENABLED,
    CTX_TG_ERROR_SENT,
)

MAX_STREAM_CHARS: int = 3900
MIN_RESPONSE_UPDATE_SECONDS: float = 1.0
MAX_PROGRESS_LINES: int = 12

TOOL_EMOJIS: dict[str, str] = {
    "browser": "🌐",
    "code": "⌨️",
    "code_execution_tool": "⌨️",
    "duckduckgo_search": "🔎",
    "read_file": "📖",
    "file": "📄",
    "knowledge_tool": "📚",
    "memory": "🧠",
    "search": "🔎",
    "search_engine": "🔎",
    "search_files": "🔎",
    "skill": "📚",
    "skill_view": "📚",
}


async def start(context: AgentContext) -> None:
    context.data.pop(CTX_TG_ERROR_SENT, None)
    # Do not pre-create a placeholder Telegram message. Wait until we have
    # real assistant text so the stream starts with meaningful content.
    if not _stream_enabled(context):
        return


async def add_tool_start(
    context: AgentContext,
    tool_name: str,
    args: dict | None = None,
) -> None:
    if not _tools_enabled(context):
        return
    label = _tool_progress_label(tool_name, args or {})
    _append_progress_line(context, f"{_tool_emoji(tool_name)} {label}")
    await _send_progress(context)


async def add_tool_done(context: AgentContext, tool_name: str, ok: bool = True) -> None:
    if not _tools_enabled(context):
        return
    if ok:
        return
    _mark_tool_failed(context, tool_name)
    await _send_progress(context)


async def update_response(context: AgentContext, response_text: str) -> None:
    if not _stream_enabled(context):
        return
    cleaned = _visible_response_text(response_text)
    if not cleaned:
        return
    context.data[CTX_TG_RESPONSE_TEXT] = response_text or ""
    now = time.time()
    last = float(context.data.get(CTX_TG_RESPONSE_LAST_UPDATE) or 0.0)
    if now - last < MIN_RESPONSE_UPDATE_SECONDS:
        return
    await _update_response_message(context, response_text or "")
    context.data[CTX_TG_RESPONSE_LAST_UPDATE] = now


async def send_intermediate_response(
    context: AgentContext,
    response_text: str,
    keyboard: list[list[dict]] | None = None,
) -> bool:
    if context.data.get(CTX_TG_RESPONSE_MESSAGE_ID):
        sent = await finalize_response(context, response_text, keyboard)
        if sent:
            _reset_progress_group(context)
        return sent

    html = _format_response(response_text)
    if not html:
        return False
    bot = _bot_instance(context)
    chat_id = context.data.get(CTX_TG_CHAT_ID)
    if not bot or not chat_id:
        return False
    try:
        sent_id = await tc.raw_send_text(
            bot.bot.token,
            int(chat_id),
            html,
            parse_mode="HTML",
            reply_markup=_keyboard_markup(keyboard),
        )
        sent = bool(sent_id)
        if sent:
            _reset_progress_group(context)
        return sent
    except Exception as e:
        PrintStyle.debug(f"Telegram intermediate response failed: {e}")
        return False


async def finalize_response(
    context: AgentContext,
    response_text: str,
    keyboard: list[list[dict]] | None = None,
) -> bool:
    message_id = context.data.get(CTX_TG_RESPONSE_MESSAGE_ID)
    if not message_id:
        return False
    ok = await _update_response_message(
        context,
        response_text or context.data.get(CTX_TG_RESPONSE_TEXT) or "",
        keyboard=keyboard,
        force=True,
    )
    if ok:
        context.data.pop(CTX_TG_RESPONSE_MESSAGE_ID, None)
        context.data.pop(CTX_TG_RESPONSE_TEXT, None)
        context.data.pop(CTX_TG_RESPONSE_LAST_UPDATE, None)
    return ok


def clear(context: AgentContext) -> None:
    for key in (
        CTX_TG_PROGRESS_LINES,
        CTX_TG_PROGRESS_MESSAGE_ID,
        CTX_TG_RESPONSE_MESSAGE_ID,
        CTX_TG_RESPONSE_TEXT,
        CTX_TG_RESPONSE_LAST_UPDATE,
    ):
        context.data.pop(key, None)


def _reset_progress_group(context: AgentContext) -> None:
    context.data.pop(CTX_TG_PROGRESS_LINES, None)
    context.data.pop(CTX_TG_PROGRESS_MESSAGE_ID, None)


def _stream_enabled(context: AgentContext) -> bool:
    value = context.get_data(CTX_TG_STREAM_ENABLED)
    return True if value is None else bool(value)


def _tools_enabled(context: AgentContext) -> bool:
    value = context.get_data(CTX_TG_TOOLS_ENABLED)
    return True if value is None else bool(value)


async def _send_progress(context: AgentContext) -> None:
    bot = _bot_instance(context)
    chat_id = context.data.get(CTX_TG_CHAT_ID)
    if not bot or not chat_id:
        return
    text = "\n".join(context.data.get(CTX_TG_PROGRESS_LINES) or [])
    if not text:
        return
    message_id = context.data.get(CTX_TG_PROGRESS_MESSAGE_ID)
    try:
        if message_id:
            await tc.raw_edit_text(bot.bot.token, int(chat_id), int(message_id), text, parse_mode=None)
            return
        sent_id = await tc.raw_send_text(
            bot.bot.token,
            int(chat_id),
            text,
            parse_mode=None,
        )
        if sent_id:
            context.data[CTX_TG_PROGRESS_MESSAGE_ID] = sent_id
    except Exception as e:
        PrintStyle.debug(f"Telegram progress update failed: {e}")


async def _ensure_response_message(context: AgentContext, text: str) -> int | None:
    message_id = context.data.get(CTX_TG_RESPONSE_MESSAGE_ID)
    if message_id:
        return int(message_id)
    html = _format_response(text)
    if not html:
        return None
    bot = _bot_instance(context)
    chat_id = context.data.get(CTX_TG_CHAT_ID)
    if not bot or not chat_id:
        return None
    sent_id = await tc.raw_send_text(
        bot.bot.token,
        int(chat_id),
        html,
        reply_to_message_id=_reply_to(context),
        parse_mode="HTML",
    )
    if sent_id:
        context.data[CTX_TG_RESPONSE_MESSAGE_ID] = sent_id
        context.data[CTX_TG_RESPONSE_LAST_UPDATE] = time.time()
    return sent_id


async def _update_response_message(
    context: AgentContext,
    text: str,
    *,
    keyboard: list[list[dict]] | None = None,
    force: bool = False,
) -> bool:
    had_message = bool(context.data.get(CTX_TG_RESPONSE_MESSAGE_ID))
    message_id = await _ensure_response_message(context, text)
    bot = _bot_instance(context)
    chat_id = context.data.get(CTX_TG_CHAT_ID)
    if not message_id or not bot or not chat_id:
        return False
    markup = _keyboard_markup(keyboard)
    html = _format_response(text)
    if not had_message and not markup and not force:
        return True
    try:
        ok = await tc.raw_edit_text(
            bot.bot.token,
            int(chat_id),
            int(message_id),
            html,
            parse_mode="HTML",
            reply_markup=markup,
        )
        if ok or force:
            return ok
        return False
    except Exception as e:
        PrintStyle.debug(f"Telegram response update failed: {e}")
        return False


def _append_progress_line(context: AgentContext, line: str) -> None:
    lines = list(context.data.get(CTX_TG_PROGRESS_LINES) or [])
    if lines and lines[-1] == line:
        return
    lines.append(line)
    context.data[CTX_TG_PROGRESS_LINES] = lines[-MAX_PROGRESS_LINES:]


def _mark_tool_failed(context: AgentContext, tool_name: str) -> None:
    lines = list(context.data.get(CTX_TG_PROGRESS_LINES) or [])
    if not lines:
        return

    label = _tool_label(tool_name)
    for index in range(len(lines) - 1, -1, -1):
        line = lines[index]
        if _line_matches_tool(line, label):
            _, _, suffix = line.partition(" ")
            lines[index] = f"❌ {suffix or label}"
            context.data[CTX_TG_PROGRESS_LINES] = lines[-MAX_PROGRESS_LINES:]
            return

    lines.append(f"❌ {label}")
    context.data[CTX_TG_PROGRESS_LINES] = lines[-MAX_PROGRESS_LINES:]


def _bot_instance(context: AgentContext):
    bot_name = context.data.get(CTX_TG_BOT)
    return get_bot(bot_name) if bot_name else None


def _reply_to(context: AgentContext) -> int | None:
    value = context.data.get(CTX_TG_REPLY_TO)
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def _tool_label(tool_name: str) -> str:
    value = (tool_name or "tool").replace("_", " ").replace("-", " ").strip()
    return value or "tool"


def _line_matches_tool(line: str, label: str) -> bool:
    _, _, suffix = line.partition(" ")
    normalized_suffix = suffix.strip().lower()
    normalized_label = label.strip().lower()
    return normalized_suffix == normalized_label or normalized_suffix.startswith(f"{normalized_label}:")


def _tool_progress_label(tool_name: str, args: dict) -> str:
    label = _tool_label(tool_name)
    detail = _tool_detail(tool_name, args)
    return f"{label}: {detail}" if detail else label


def _tool_detail(tool_name: str, args: dict) -> str:
    if not isinstance(args, dict) or not args:
        return ""

    normalized = (tool_name or "").strip().lower()
    if "search" in normalized:
        return _first_arg(args, ("query", "q", "search", "term", "keywords", "pattern"))
    if "browser" in normalized:
        return _first_arg(args, ("url", "link", "query", "action"))
    if "file" in normalized:
        return _first_arg(args, ("path", "file", "filename", "query", "pattern"))
    if "skill" in normalized:
        return _first_arg(args, ("skill", "name", "query", "path"))

    return _first_arg(args, ("action", "method", "operation"))


def _first_arg(args: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = args.get(key)
        if value is None:
            continue
        text = _compact_detail(value)
        if text:
            return text
    return ""


def _compact_detail(value: object) -> str:
    if isinstance(value, (list, tuple)):
        parts = [_compact_detail(item) for item in value[:2]]
        text = ", ".join(part for part in parts if part)
        if len(value) > 2:
            text = f"{text}, ..."
    elif isinstance(value, dict):
        return ""
    else:
        text = str(value).strip()

    text = re.sub(r"\s+", " ", text).strip().strip("\"'")
    if len(text) > 80:
        text = f"{text[:77].rstrip()}..."
    return text


def _tool_emoji(tool_name: str) -> str:
    normalized = (tool_name or "").strip().lower()
    for key, emoji in TOOL_EMOJIS.items():
        if key in normalized:
            return emoji
    return "🛠️"


def _format_response(text: str) -> str:
    value = _visible_response_text(text)
    if not value:
        return ""
    return tc.md_to_telegram_html(value)


def _strip_incomplete_tool_markup(text: str) -> str:
    value = text.lstrip()
    value = re.sub(r"^<[^>\n]{0,80}$", "", value)
    value = re.sub(r"^```(?:json|xml)?\s*$", "", value, flags=re.IGNORECASE)
    return value


def _visible_response_text(text: str) -> str:
    value = _trim(text or "")
    return _strip_incomplete_tool_markup(value)


def _trim(text: str) -> str:
    if len(text) <= MAX_STREAM_CHARS:
        return text
    return text[-MAX_STREAM_CHARS:]


def _keyboard_markup(keyboard: list[list[dict]] | None) -> dict | None:
    if not keyboard:
        return None
    rows: list[list[dict[str, str]]] = []
    for row in keyboard:
        out_row: list[dict[str, str]] = []
        for button in row:
            text = str(button.get("text") or "")[:64]
            if not text:
                continue
            if button.get("url"):
                out_row.append({"text": text, "url": str(button["url"])})
            else:
                data = str(button.get("callback_data", text))
                out_row.append({"text": text, "callback_data": data[:64]})
        if out_row:
            rows.append(out_row)
    return {"inline_keyboard": rows} if rows else None
