import os
import re

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from helpers.errors import format_error
from helpers.print_style import PrintStyle

_UNSET = object()  # sentinel: "not provided" (lets Bot default apply)

# Text messages

MAX_MESSAGE_LENGTH: int = 4096  # Telegram message length limit


async def send_text(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_to_message_id: int | None = None,
    parse_mode: object = _UNSET,
) -> int | None:
    """Send text message, splitting if too long. Returns last message_id or None on error.

    parse_mode behaviour:
      - _UNSET (default): omitted from send_message → Bot's DefaultBotProperties applies.
      - None: explicitly no formatting.
      - "HTML"/"Markdown"/etc.: that specific mode.
    """
    try:
        chunks = _split_text(text, MAX_MESSAGE_LENGTH)
        last_msg_id = None
        pm_kwargs: dict = {} if parse_mode is _UNSET else {"parse_mode": parse_mode}
        for chunk in chunks:
            try:
                msg = await bot.send_message(
                    chat_id=chat_id,
                    text=chunk,
                    reply_to_message_id=reply_to_message_id,
                    **pm_kwargs,
                )
                last_msg_id = msg.message_id
            except TelegramBadRequest:
                # Retry as plain text, stripping HTML tags
                plain = re.sub(r"<[^>]+>", "", chunk)
                msg = await bot.send_message(
                    chat_id=chat_id,
                    text=plain,
                    reply_to_message_id=reply_to_message_id,
                    parse_mode=None,
                )
                last_msg_id = msg.message_id
        return last_msg_id
    except Exception as e:
        PrintStyle.error(f"Telegram send_text failed: {format_error(e)}")
        return None

# Files and images

async def send_file(
    bot: Bot,
    chat_id: int,
    file_path: str,
    caption: str = "",
    reply_to_message_id: int | None = None,
) -> int | None:
    """Send a file from local path. Returns message_id or None on error."""
    try:
        if not os.path.isfile(file_path):
            PrintStyle.error(f"Telegram: file not found: {file_path}")
            return None
        input_file = FSInputFile(file_path)
        msg = await bot.send_document(
            chat_id=chat_id,
            document=input_file,
            caption=caption[:1024] if caption else None,
            reply_to_message_id=reply_to_message_id,
        )
        return msg.message_id
    except Exception as e:
        PrintStyle.error(f"Telegram send_file failed: {format_error(e)}")
        return None


async def send_photo(
    bot: Bot,
    chat_id: int,
    photo_path: str,
    caption: str = "",
    reply_to_message_id: int | None = None,
) -> int | None:
    """Send a photo from local path. Returns message_id or None on error."""
    try:
        if not os.path.isfile(photo_path):
            PrintStyle.error(f"Telegram: photo not found: {photo_path}")
            return None
        input_file = FSInputFile(photo_path)
        msg = await bot.send_photo(
            chat_id=chat_id,
            photo=input_file,
            caption=caption[:1024] if caption else None,
            reply_to_message_id=reply_to_message_id,
        )
        return msg.message_id
    except Exception as e:
        PrintStyle.error(f"Telegram send_photo failed: {format_error(e)}")
        return None


# Inline keyboards

def build_inline_keyboard(
    buttons: list[list[dict]],
) -> InlineKeyboardMarkup:
    """Build inline keyboard from a list of rows.
    Each row is a list of dicts with keys: text, callback_data or url.
    """
    rows = []
    for row in buttons:
        row_buttons = []
        for btn in row:
            if "url" in btn:
                row_buttons.append(InlineKeyboardButton(
                    text=btn["text"], url=btn["url"],
                ))
            else:
                row_buttons.append(InlineKeyboardButton(
                    text=btn["text"],
                    callback_data=btn.get("callback_data", btn["text"]),
                ))
        rows.append(row_buttons)
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_text_with_keyboard(
    bot: Bot,
    chat_id: int,
    text: str,
    buttons: list[list[dict]],
    reply_to_message_id: int | None = None,
    parse_mode: object = _UNSET,
) -> int | None:
    """Send text with inline keyboard buttons."""
    try:
        keyboard = build_inline_keyboard(buttons)
        pm_kwargs: dict = {} if parse_mode is _UNSET else {"parse_mode": parse_mode}
        msg = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            reply_to_message_id=reply_to_message_id,
            **pm_kwargs,
        )
        return msg.message_id
    except Exception as e:
        PrintStyle.error(f"Telegram send_text_with_keyboard failed: {format_error(e)}")
        return None

# Typing indicator

async def send_typing(bot: Bot, chat_id: int):
    """Send 'typing...' action to chat."""
    try:
        await bot.send_chat_action(chat_id=chat_id, action="typing")
    except Exception:
        pass

# File download

async def download_file(
    bot: Bot,
    file_id: str,
    destination: str,
) -> str | None:
    """Download a file by file_id to destination path. Returns path or None on error."""
    try:
        file = await bot.get_file(file_id)
        if not file.file_path:
            return None
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        await bot.download_file(file.file_path, destination)
        return destination
    except Exception as e:
        PrintStyle.error(f"Telegram download failed: {format_error(e)}")
        return None

# Helpers

def _split_text(text: str, max_len: int) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to split at newline
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1 or split_at < max_len // 2:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def is_image_file(path: str) -> bool:
    _, ext = os.path.splitext(path.lower())
    return ext in _IMAGE_EXTENSIONS


def md_to_telegram_html(text: str) -> str:
    """Convert Markdown to Telegram-compatible HTML."""
    stash: list[str] = []

    def _put(html: str) -> str:
        stash.append(html)
        return f"\x00B{len(stash) - 1}\x00"

    def _esc(t: str) -> str:
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Stash code blocks & inline code
    def _code_block(m):
        lang, body = m.group(1), m.group(2).rstrip("\n")
        if lang:
            return _put(f'<pre><code class="language-{lang}">{_esc(body)}</code></pre>')
        return _put(f"<pre>{_esc(body)}</pre>")

    text = re.sub(r"(?:```|~~~)(\w*)\n?(.*?)(?:```|~~~)", _code_block, text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", lambda m: _put(f"<code>{_esc(m.group(1))}</code>"), text)

    # Strip unsupported syntax
    text = _strip_tables(text)
    text = re.sub(r"^[ \t]*[-*_=]{3,}[ \t]*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"[\1](\2)", text)

    # Stash links
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: _put(
            f'<a href="{m.group(2).replace("&", "&amp;").replace(chr(34), "&quot;")}">{_esc(m.group(1))}</a>'
        ),
        text,
    )

    # Escape HTML & apply inline formatting
    text = _esc(text)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_([^_]+?)_(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)
    text = re.sub(r"^#{1,6}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # Block-level formatting
    text = _convert_blockquotes(text)
    text = _convert_lists(text)

    # Restore stash
    for i, block in enumerate(stash):
        text = text.replace(f"\x00B{i}\x00", block)
    return text



_TABLE_RE = re.compile(r"^\|(.+)\|$")
_TABLE_SEP = re.compile(r"^[\s|:-]+$")


def _strip_tables(text: str) -> str:
    """Strip Markdown table pipe syntax, keeping cell content as plain text."""
    out: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if _TABLE_SEP.match(stripped):
            continue
        m = _TABLE_RE.match(stripped)
        if m:
            out.append("  ".join(c.strip() for c in m.group(1).split("|")))
        else:
            out.append(line)
    return "\n".join(out)


_LIST_RE = re.compile(r"^( *)([-*+]|\d+\.)\s+(.*)$")
_BULLETS = ("\u2022", "\u25e6", "\u25aa")


def _convert_lists(text: str) -> str:
    """Convert Markdown list markers to Unicode bullets."""
    out: list[str] = []
    for line in text.split("\n"):
        m = _LIST_RE.match(line)
        if m:
            depth = len(m.group(1)) // 2
            marker, content = m.group(2), m.group(3)
            px = "  " * depth
            if marker.rstrip(".").isdigit():
                out.append(f"{px}{marker} {content}")
            else:
                out.append(f"{px}{_BULLETS[min(depth, len(_BULLETS) - 1)]} {content}")
        else:
            out.append(line)
    return "\n".join(out)


def _convert_blockquotes(text: str) -> str:
    """Convert Markdown blockquotes to Telegram <blockquote> tags."""
    out: list[str] = []
    buf: list[str] = []

    def _flush():
        if buf:
            out.append("<blockquote>" + "\n".join(buf) + "</blockquote>")
            buf.clear()

    for line in text.split("\n"):
        m = re.match(r"^&gt;\s?(.*)", line)
        if m:
            buf.append(m.group(1))
        else:
            _flush()
            out.append(line)
    _flush()
    return "\n".join(out)
