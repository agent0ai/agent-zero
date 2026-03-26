"""
IMAP/Exchange email reader. 

No agent/tool dependencies.
"""

import asyncio
import email
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.header import decode_header
from email.message import Message as EmailMessage
from fnmatch import fnmatch

import html2text
from bs4 import BeautifulSoup
from imapclient import IMAPClient

from helpers import files
from helpers.errors import format_error
from helpers.print_style import PrintStyle


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------

@dataclass
class InboundMessage:
    sender: str
    subject: str
    body: str
    attachments: list[str] = field(default_factory=list)
    message_id: str = ""
    in_reply_to: str = ""
    references: str = ""


# ------------------------------------------------------------------
# IMAP connection
# ------------------------------------------------------------------

async def connect_imap(
    server: str,
    port: int = 993,
    username: str = "",
    password: str = "",
    ssl: bool = True,
    timeout: int = 30,
) -> IMAPClient:
    loop = asyncio.get_event_loop()

    def _sync():
        client = IMAPClient(server, port=port, ssl=ssl, timeout=timeout)
        client._imap._maxline = 100000  # type: ignore[attr-defined]
        client.login(username, password)
        return client

    return await loop.run_in_executor(None, _sync)


async def disconnect_imap(client: IMAPClient) -> None:
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, client.logout)
    except Exception as e:
        PrintStyle.error(f"IMAP disconnect error: {format_error(e)}")


# ------------------------------------------------------------------
# Fetch messages
# ------------------------------------------------------------------

async def fetch_new(
    client: IMAPClient,
    download_folder: str,
    last_uid: int = 0,
    sender_whitelist: list[str] | None = None,
    max_messages: int = 10,
) -> tuple[list[InboundMessage], int]:
    """Fetch emails newer than last_uid. Returns (messages, new_last_uid)."""
    loop = asyncio.get_event_loop()

    def _search():
        client.select_folder("INBOX")
        # Use Gmail category filter if supported, otherwise plain UNSEEN
        try:
            return client.gmail_search("category:primary is:unread")
        except Exception:
            return client.search(["UNSEEN"])  # type: ignore[arg-type]

    msg_ids = await loop.run_in_executor(None, _search)
    if not msg_ids:
        return [], last_uid

    # Filter out already-seen UIDs
    if last_uid > 0:
        msg_ids = [uid for uid in msg_ids if uid > last_uid]

    if not msg_ids:
        return [], last_uid

    new_last_uid = max(msg_ids)

    # Cap to most recent
    if len(msg_ids) > max_messages:
        PrintStyle.standard(
            f"Email: {len(msg_ids)} new, processing latest {max_messages}"
        )
        msg_ids = msg_ids[-max_messages:]
    else:
        PrintStyle.standard(f"Email: found {len(msg_ids)} new messages")

    results: list[InboundMessage] = []

    for msg_id in msg_ids:
        try:
            msg = await _fetch_single(client, msg_id, download_folder, sender_whitelist)
            if msg:
                results.append(msg)
        except Exception as e:
            PrintStyle.error(f"Email: error processing message {msg_id}: {format_error(e)}")
    return results, new_last_uid


async def get_highest_uid(client: IMAPClient) -> int:
    """Get the highest UID in inbox without fetching any messages."""
    loop = asyncio.get_event_loop()

    def _search():
        client.select_folder("INBOX")
        uids = client.search(["ALL"])  # type: ignore[arg-type]
        return max(uids) if uids else 0

    return await loop.run_in_executor(None, _search)


async def fetch_unread_since(
    client: IMAPClient,
    download_folder: str,
    days: int,
    sender_whitelist: list[str] | None = None,
    max_messages: int = 10,
) -> tuple[list[InboundMessage], int]:
    """Fetch unread emails from the last N days. Returns (messages, highest_uid)."""
    loop = asyncio.get_event_loop()
    since_date = datetime.now() - timedelta(days=days)

    def _search():
        client.select_folder("INBOX")
        try:
            return client.gmail_search(
                f"category:primary is:unread after:{since_date.strftime('%Y/%m/%d')}"
            )
        except Exception:
            return client.search(["UNSEEN", "SINCE", since_date.date()])  # type: ignore[arg-type]

    msg_ids = await loop.run_in_executor(None, _search)
    if not msg_ids:
        return [], 0

    highest_uid = max(msg_ids)

    if len(msg_ids) > max_messages:
        PrintStyle.standard(
            f"Email: {len(msg_ids)} unread, processing latest {max_messages}"
        )
        msg_ids = msg_ids[-max_messages:]
    else:
        PrintStyle.standard(
            f"Email: found {len(msg_ids)} unread messages from last {days} days"
        )

    results: list[InboundMessage] = []
    for msg_id in msg_ids:
        try:
            msg = await _fetch_single(client, msg_id, download_folder, sender_whitelist)
            if msg:
                results.append(msg)
        except Exception as e:
            PrintStyle.error(
                f"Email: error processing message {msg_id}: {format_error(e)}"
            )

    return results, highest_uid


async def _fetch_single(
    client: IMAPClient,
    msg_id: int,
    download_folder: str,
    sender_whitelist: list[str] | None,
) -> InboundMessage | None:
    loop = asyncio.get_event_loop()

    def _sync_fetch():
        data = client.fetch([msg_id], ["RFC822"])[msg_id]
        # Explicitly mark as read — RFC822 fetch doesn't always set \Seen on all servers
        client.add_flags([msg_id], [b"\\Seen"])
        return data

    raw = await loop.run_in_executor(None, _sync_fetch)
    email_data = raw.get(b"RFC822")
    if not email_data:
        return None

    email_msg = email.message_from_bytes(email_data)  # type: ignore[arg-type]

    sender = _decode_header(email_msg.get("From", ""))
    if _is_noreply(sender):
        return None
    if sender_whitelist and not _matches_whitelist(sender, sender_whitelist):
        return None

    subject = _decode_header(email_msg.get("Subject", ""))
    message_id = email_msg.get("Message-ID", "")
    in_reply_to = email_msg.get("In-Reply-To", "")
    references = email_msg.get("References", "")

    body, attachments = await _parse_body(email_msg, download_folder)

    return InboundMessage(
        sender=sender,
        subject=subject,
        body=body,
        attachments=attachments,
        message_id=message_id,
        in_reply_to=in_reply_to,
        references=references,
    )


# ------------------------------------------------------------------
# Exchange connection
# ------------------------------------------------------------------

async def connect_exchange(
    server: str,
    username: str,
    password: str,
):
    from exchangelib import Account, Configuration, Credentials, DELEGATE

    loop = asyncio.get_event_loop()

    def _sync():
        creds = Credentials(username=username, password=password)
        config = Configuration(server=server, credentials=creds)
        return Account(
            primary_smtp_address=username,
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )

    return await loop.run_in_executor(None, _sync)


async def fetch_unread_exchange(
    account,
    download_folder: str,
    sender_whitelist: list[str] | None = None,
    since_days: int = 0,
) -> list[InboundMessage]:
    from exchangelib import Q

    loop = asyncio.get_event_loop()

    def _sync():
        q = Q(is_read=False)
        if since_days > 0:
            since = datetime.now(tz=account.default_timezone) - timedelta(days=since_days)
            q &= Q(datetime_received__gte=since)
        return list(account.inbox.filter(q))

    items = await loop.run_in_executor(None, _sync)
    results: list[InboundMessage] = []

    for item in items:
        sender = str(item.sender.email_address) if item.sender else ""
        if _is_noreply(sender):
            continue
        if sender_whitelist and not _matches_whitelist(sender, sender_whitelist):
            continue

        body = str(item.text_body or item.body or "")
        if item.body and str(item.body).strip().startswith("<"):
            body = _html_to_text(str(item.body))

        attachment_paths: list[str] = []
        if item.attachments:
            for att in item.attachments:
                if hasattr(att, "content") and att.name:
                    path = await _save_attachment(att.name, att.content, download_folder)
                    attachment_paths.append(path)

        results.append(InboundMessage(
            sender=sender,
            subject=str(item.subject or ""),
            body=body,
            attachments=attachment_paths,
            message_id=str(getattr(item, "message_id", "") or ""),
            in_reply_to=str(getattr(item, "in_reply_to", "") or ""),
            references="",
        ))

    return results


# ------------------------------------------------------------------
# Parsing helpers
# ------------------------------------------------------------------

async def _parse_body(
    email_msg: EmailMessage,
    download_folder: str,
) -> tuple[str, list[str]]:
    body = ""
    attachments: list[str] = []
    cid_map: dict[str, str] = {}
    body_parts: list[str] = []

    if email_msg.is_multipart():
        for part in email_msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if part.get_content_maintype() == "multipart":
                continue

            if "attachment" in disposition or part.get("Content-ID"):
                filename = part.get_filename()
                if filename:
                    filename = _decode_header(filename)
                    content = part.get_payload(decode=True)
                    if isinstance(content, bytes):
                        path = await _save_attachment(filename, content, download_folder)
                        attachments.append(path)
                        cid = part.get("Content-ID")
                        if cid:
                            cid_map[cid.strip("<>")] = path
                        
                        if not cid:
                            body_parts.append(f"\n[attachment://{path}]\n")

            elif content_type == "text/plain":
                if not body:
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    body = payload.decode(charset, errors="ignore") if isinstance(payload, bytes) else ""
                    body_parts.append(body)

            elif content_type == "text/html":
                if not body:
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    html = payload.decode(charset, errors="ignore") if isinstance(payload, bytes) else ""
                    body = _html_to_text(html, cid_map)
                    body_parts.append(body)

        if len(body_parts) > 1:
            body = "".join(body_parts)
    else:
        content_type = email_msg.get_content_type()
        charset = email_msg.get_content_charset() or "utf-8"
        content = email_msg.get_payload(decode=True)
        if isinstance(content, bytes):
            if content_type == "text/html":
                body = _html_to_text(content.decode(charset, errors="ignore"))
            else:
                body = content.decode(charset, errors="ignore")

    body = _strip_quoted_reply(body)
    return body, attachments


def _strip_quoted_reply(text: str) -> str:
    """Remove quoted reply chains (e.g. 'On ... wrote:' + '>' lines)."""
    if not text:
        return text
    lines = text.splitlines()
    cut = len(lines)
    for i, line in enumerate(lines):
        # Match "On <date> <someone> wrote:" pattern
        if re.match(r"^On .+ wrote:\s*$", line.strip()):
            # Verify next non-empty lines are quoted
            rest = [l for l in lines[i + 1:] if l.strip()]
            if not rest or rest[0].strip().startswith(">"):
                cut = i
                break
    # Also strip trailing blank lines before the cut
    while cut > 0 and not lines[cut - 1].strip():
        cut -= 1
    return "\n".join(lines[:cut]).strip()


def _html_to_text(html_content: str, cid_map: dict[str, str] | None = None) -> str:
    if cid_map:
        soup = BeautifulSoup(html_content, "html.parser")
        for img in soup.find_all("img"):
            src = str(img.get("src", "")) # type: ignore
            if src.startswith("cid:"):
                cid = src[4:]
                if cid in cid_map:
                    img.replace_with(soup.new_string(f"[attachment://{cid_map[cid]}]"))
        html_content = str(soup)

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0
    text = h.handle(html_content)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


async def _save_attachment(filename: str, content: bytes, download_folder: str) -> str:
    filename = files.safe_file_name(filename)
    name, ext = os.path.splitext(filename)
    unique = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    rel_path = os.path.join(download_folder, unique)
    from helpers import runtime
    from plugins._email_integration.helpers.attachment_writer import write_attachment
    
    import base64
    content_b64 = base64.b64encode(content).decode()
    
    result = await runtime.call_development_function(
        write_attachment, rel_path, content_b64
    )
    if result.get("error"):
        from helpers.print_style import PrintStyle
        PrintStyle.error(f"Failed to save attachment {filename}: {result['error']}")
        
    return result.get("path", files.get_abs_path(rel_path))


def _decode_header(header: str) -> str:
    if not header:
        return ""
    parts = []
    for part, encoding in decode_header(header):
        if isinstance(part, bytes):
            parts.append(part.decode(encoding or "utf-8", errors="ignore"))
        else:
            parts.append(str(part))
    return " ".join(parts)


def _is_noreply(sender: str) -> bool:
    addr = sender.lower()
    match = re.search(r"<([^>]+)>", addr)
    if match:
        addr = match.group(1)
    local = addr.split("@")[0] if "@" in addr else addr
    return local in (
        "noreply", "no-reply", "no_reply",
        "donotreply", "do-not-reply", "do_not_reply",
        "mailer-daemon", "postmaster",
    )


def _matches_whitelist(sender: str, whitelist: list[str]) -> bool:
    sender_email = _extract_email_from_sender(sender.lower())
    for pattern in whitelist:
        if fnmatch(sender_email, pattern.lower()):
            return True
    return False


def _extract_email_from_sender(sender: str) -> str:
    """Extract email address from sender string.
    
    Handles formats like:
    - "email@example.com"
    - "Name <email@example.com>"
    - "\"Display Name\" <email@example.com>"
    
    Uses content inside angle brackets as authoritative to prevent spoofing
    by fake emails in the display name (e.g., "John ceo@company.com <real@email.com>").
    """
    import re
    # Look for email inside angle brackets - this is the authoritative source
    match = re.search(r"<([^>]+)>", sender)
    if match:
        email = match.group(1).strip()
        # Validate it looks like an email
        if re.match(r"^[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+$", email):
            return email
    
    # No angle brackets - extract email from the whole string
    # This handles plain "email@example.com" or malformed input
    email_match = re.search(r"[^\s<>]+@[^\s<>]+\.[^\s<>]+", sender)
    if email_match:
        return email_match.group(0)
    
    # Fallback: return the whole string (will likely fail pattern match)
    return sender
