"""
WhatsApp handler — orchestrates poll, dispatch, and reply.

Requires agent context.
"""

import asyncio
import base64
import os
import re
import uuid

from agent import Agent, AgentContext, UserMessage
from helpers import plugins, files, runtime
from helpers import message_queue as mq
from helpers.persist_chat import save_tmp_chat
from helpers.print_style import PrintStyle
from helpers.errors import format_error
from initialize import initialize_agent

from plugins._whatsapp_integration.helpers import wa_client
from plugins._whatsapp_integration.helpers import bridge_manager
from plugins._whatsapp_integration.helpers.number_utils import (
    normalize_allowed_numbers,
    normalize_number,
)


PLUGIN_NAME = "_whatsapp_integration"
MEDIA_FOLDER = "usr/whatsapp/media"

# Context data keys (no underscore prefix — must persist across restarts)
CTX_WA_CHAT_ID = "wa_chat_id"
CTX_WA_SENDER_NAME = "wa_sender_name"
CTX_WA_SENDER_NUMBER = "wa_sender_number"
CTX_WA_IS_GROUP = "wa_is_group"
CTX_WA_LAST_BODY = "wa_last_body"
CTX_WA_LAST_MSG_ID = "wa_last_msg_id"
# Transient — consumed per-reply, not persisted
CTX_WA_ATTACHMENTS = "_wa_response_attachments"
CTX_WA_REPLY_TO = "_wa_reply_to"
CTX_WA_TYPING_ACTIVE = "_wa_typing_active"

# Poll task — lives here (not in extension module) because
# extension modules are re-executed on each job_loop tick,
# which would reset module-level state and orphan running tasks.
_poll_task: asyncio.Task | None = None  # type: ignore[type-arg]


# ------------------------------------------------------------------
# Poll loop
# ------------------------------------------------------------------

async def _refresh_typing(base_url: str) -> None:
    """Re-send composing for all contexts with active typing flag."""
    for ctx in AgentContext._contexts.values():
        if not isinstance(ctx, AgentContext):
            continue
        if not ctx.data.get(CTX_WA_TYPING_ACTIVE):
            continue
        chat_id = ctx.data.get(CTX_WA_CHAT_ID, "")
        if chat_id:
            await wa_client.send_typing(base_url, chat_id)


async def poll_messages(config: dict) -> None:
    if not config.get("enabled", False):
        return
    if PLUGIN_NAME not in plugins.get_enabled_plugins(None):
        return

    port = int(config.get("bridge_port", 3100))
    base_url = bridge_manager.get_bridge_url(port)

    # Refresh typing indicator for active sessions (beats 25s WhatsApp timeout)
    await _refresh_typing(base_url)

    try:
        messages = await wa_client.get_messages(base_url)
    except Exception as e:
        PrintStyle.error(f"WhatsApp poll error: {format_error(e)}")
        return

    if not messages:
        return

    # Allowed-numbers filtering is authoritative in Python.
    allowed_set = normalize_allowed_numbers(config.get("allowed_numbers"))

    for msg in messages:
        try:
            # Filter by allowed numbers if configured
            if allowed_set:
                sender_num = normalize_number(msg.get("senderNumber", "") or msg.get("senderId", ""))
                if sender_num not in allowed_set:
                    PrintStyle.debug(
                        f"WhatsApp: ignored message from {sender_num} "
                        f"(senderId: {msg.get('senderId', '')}, allowed: {allowed_set})"
                    )
                    continue
            await _dispatch_message(config, msg)
        except Exception as e:
            PrintStyle.error(f"WhatsApp dispatch error: {format_error(e)}")


# ------------------------------------------------------------------
# Dispatch a single inbound message
# ------------------------------------------------------------------

async def _dispatch_message(config: dict, msg: dict) -> None:
    chat_id = msg.get("chatId", "")
    is_group = msg.get("isGroup", False)

    # Group filtering: skip unless allow_group enabled AND bot was mentioned or replied to
    if is_group:
        if not config.get("allow_group", False):
            PrintStyle.debug(f"WhatsApp: skipping group message (allow_group disabled)")
            return
        if not msg.get("mentionedMe", False) and not msg.get("repliedToMe", False):
            PrintStyle.debug(f"WhatsApp: skipping group message (not mentioned or replied to)")
            return

    # Show typing indicator immediately so user sees activity
    port = int(config.get("bridge_port", 3100))
    base_url = bridge_manager.get_bridge_url(port)
    await wa_client.send_typing(base_url, chat_id)

    existing = _find_chats_by_jid(chat_id)

    if existing:
        # Continue most recent chat for this JID
        await _route_to_chat(msg, existing[0])
    else:
        await _start_new_chat(config, msg)


# ------------------------------------------------------------------
# Chat creation and routing
# ------------------------------------------------------------------

async def _start_new_chat(config: dict, msg: dict) -> None:
    from helpers import projects

    sender_name = msg.get("senderName", "Unknown")
    sender_number = msg.get("senderNumber", "") or normalize_number(msg.get("senderId", ""))
    chat_id = msg.get("chatId", "")
    is_group = msg.get("isGroup", False)

    agent_config = initialize_agent()
    context = AgentContext(agent_config, name=f"WhatsApp: {sender_name[:50]}")

    context.data[CTX_WA_CHAT_ID] = chat_id
    context.data[CTX_WA_SENDER_NAME] = sender_name
    context.data[CTX_WA_SENDER_NUMBER] = sender_number
    context.data[CTX_WA_IS_GROUP] = is_group
    context.data[CTX_WA_LAST_BODY] = msg.get("body", "")
    context.data[CTX_WA_LAST_MSG_ID] = msg.get("messageId", "")
    context.data[CTX_WA_TYPING_ACTIVE] = True

    project = config.get("project", "")
    if project:
        projects.activate_project(context.id, project)

    save_tmp_chat(context)

    user_msg = _build_user_message(context.agent0, msg)
    system_ctx = context.agent0.read_prompt("fw.wa.system_context.md")

    msg_id = str(uuid.uuid4())
    media_urls = msg.get("mediaUrls", [])
    attachments = await _save_incoming_media(media_urls) if media_urls else []
    mq.log_user_message(
        context, user_msg, attachments, message_id=msg_id, source=" (whatsapp)",
    )
    context.communicate(UserMessage(
        message=user_msg,
        system_message=[system_ctx],
        attachments=attachments,
        id=msg_id,
    ))

    PrintStyle.success(
        f"WhatsApp: new chat {context.id} for {sender_name} ({sender_number})"
    )


async def _route_to_chat(
    msg: dict, context_id: str,
) -> None:
    context = AgentContext.get(context_id)
    if not context:
        return

    context.data[CTX_WA_LAST_BODY] = msg.get("body", "")
    context.data[CTX_WA_LAST_MSG_ID] = msg.get("messageId", "")
    context.data[CTX_WA_TYPING_ACTIVE] = True

    user_msg = _build_user_message(context.agent0, msg)
    msg_id = str(uuid.uuid4())
    media_urls = msg.get("mediaUrls", [])
    attachments = await _save_incoming_media(media_urls) if media_urls else []
    mq.log_user_message(
        context, user_msg, attachments, message_id=msg_id, source=" (whatsapp)",
    )
    context.communicate(UserMessage(
        message=user_msg,
        attachments=attachments,
        id=msg_id,
    ))

    save_tmp_chat(context)
    PrintStyle.info(f"WhatsApp: continuing chat {context_id}")


# ------------------------------------------------------------------
# Chat discovery
# ------------------------------------------------------------------

def _find_chats_by_jid(chat_id: str) -> list[str]:
    """Return context IDs for chats matching the given WhatsApp JID, newest first."""
    results = []
    for ctx_id, ctx in AgentContext._contexts.items():
        if not isinstance(ctx, AgentContext):
            continue
        if ctx.data.get(CTX_WA_CHAT_ID) != chat_id:
            continue
        results.append(ctx_id)

    results.sort(reverse=True)
    return results


# ------------------------------------------------------------------
# Markdown to WhatsApp formatting
# ------------------------------------------------------------------

def _md_to_whatsapp(text: str) -> str:
    """Convert markdown formatting to WhatsApp formatting."""
    # Protect code blocks from conversion
    code_blocks: list[str] = []
    def _save_code(m: re.Match) -> str:
        code_blocks.append(m.group(0))
        return f"\x00CB{len(code_blocks) - 1}\x00"
    text = re.sub(r"```[\s\S]*?```", _save_code, text)

    # Protect inline code
    inline_codes: list[str] = []
    def _save_inline(m: re.Match) -> str:
        inline_codes.append(m.group(0))
        return f"\x00IC{len(inline_codes) - 1}\x00"
    text = re.sub(r"`[^`]+`", _save_inline, text)

    # Bold+italic ***text*** → *_text_*
    text = re.sub(r"\*{3}(.+?)\*{3}", r"*_\1_*", text)
    # Bold **text** or __text__ → *text*
    text = re.sub(r"\*{2}(.+?)\*{2}", r"*\1*", text)
    text = re.sub(r"__(.+?)__", r"*\1*", text)
    # Italic _text_ stays _text_ (same in WhatsApp)
    # Strikethrough ~~text~~ → ~text~
    text = re.sub(r"~~(.+?)~~", r"~\1~", text)
    # Headings → bold
    text = re.sub(r"^#{1,6}\s+(.+)$", r"*\1*", text, flags=re.MULTILINE)

    # Restore code blocks and inline code
    for i, block in enumerate(code_blocks):
        text = text.replace(f"\x00CB{i}\x00", block)
    for i, code in enumerate(inline_codes):
        text = text.replace(f"\x00IC{i}\x00", code)

    return text


# ------------------------------------------------------------------
# Message builders
# ------------------------------------------------------------------

def _build_user_message(agent: Agent, msg: dict) -> str:
    sender_name = msg.get("senderName", "Unknown")
    sender_number = msg.get("senderNumber", "") or normalize_number(msg.get("senderId", ""))
    is_group = msg.get("isGroup", False)
    prompt = "fw.wa.user_message_group.md" if is_group else "fw.wa.user_message.md"
    text = agent.read_prompt(
        prompt,
        sender_name=sender_name,
        sender_number=sender_number,
        group_name=msg.get("chatName", ""),
        message_id=msg.get("messageId", ""),
        body=msg.get("body", ""),
    )
    return text


# ------------------------------------------------------------------
# Reply sending (called from process_chain_end extension)
# ------------------------------------------------------------------

async def send_wa_reply(
    context: AgentContext,
    response_text: str,
    attachments: list[str] | None = None,
    reply_to: str = "",
    keep_typing: bool = False,
) -> str | None:
    chat_id = context.data.get(CTX_WA_CHAT_ID)
    if not chat_id:
        return "No WhatsApp chat ID"

    config = plugins.get_plugin_config(PLUGIN_NAME) or {}
    port = int(config.get("bridge_port", 3100))
    base_url = bridge_manager.get_bridge_url(port)

    # For group chats, auto-reply to last received message if no explicit reply_to
    if not reply_to and context.data.get(CTX_WA_IS_GROUP):
        reply_to = context.data.get(CTX_WA_LAST_MSG_ID, "")

    # Convert markdown to WhatsApp formatting
    response_text = _md_to_whatsapp(response_text)

    # Prefix response in self-chat mode so user can distinguish agent messages
    mode = config.get("mode", "self-chat")
    if mode == "self-chat":
        response_text = context.agent0.read_prompt(
            "fw.wa.self_chat_prefix.md", response_text=response_text,
        )

    # Send text
    try:
        result = await wa_client.send_message(base_url, chat_id, response_text, reply_to=reply_to)
        if result.get("error"):
            return result["error"]
    except Exception as e:
        return str(e)

    # Send attachments via RFC (files may live in execution runtime)
    if attachments:
        host_paths = await _read_attachments_to_host(attachments)
        for host_path in host_paths:
            try:
                result = await wa_client.send_media(
                    base_url, chat_id, host_path,
                )
                if result.get("error"):
                    PrintStyle.warning(f"WhatsApp: attachment error: {result['error']}")
            except Exception as e:
                PrintStyle.warning(f"WhatsApp: attachment error: {e}")

    # Typing: restart if agent is still working, stop if final reply
    if keep_typing:
        await wa_client.send_typing(base_url, chat_id)
    else:
        await wa_client.send_typing(base_url, chat_id, paused=True)
        context.data[CTX_WA_TYPING_ACTIVE] = False

    return None


# ------------------------------------------------------------------
# Attachment reading (via RFC into execution runtime)
# ------------------------------------------------------------------

async def _read_attachments_to_host(
    paths: list[str],
) -> list[str]:
    """Read files from execution runtime and write to host media cache."""
    from plugins._whatsapp_integration.helpers.attachment_reader import read_attachment

    host_paths: list[str] = []
    for path in paths:
        data = await runtime.call_development_function(read_attachment, path)
        if data["error"]:
            PrintStyle.warning(f"WhatsApp attachment: {data['error']}")
            continue
        # Write decoded bytes to host-side media cache
        host_path = os.path.join(
            files.get_abs_path(MEDIA_FOLDER), data["name"],
        )
        os.makedirs(os.path.dirname(host_path), exist_ok=True)
        with open(host_path, "wb") as f:
            f.write(base64.b64decode(data["content_b64"]))
        host_paths.append(host_path)
    return host_paths


async def _save_incoming_media(
    media_urls: list[str],
) -> list[str]:
    """Save incoming media files into execution runtime via RFC."""
    from plugins._whatsapp_integration.helpers.attachment_writer import write_attachment

    runtime_paths: list[str] = []
    for host_path in media_urls:
        if not os.path.isfile(host_path):
            continue
        name = os.path.basename(host_path)
        with open(host_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode()
        rel_path = os.path.join(MEDIA_FOLDER, name)
        result = await runtime.call_development_function(
            write_attachment, rel_path, content_b64,
        )
        if result.get("error"):
            PrintStyle.warning(f"WhatsApp media save: {result['error']}")
            runtime_paths.append(host_path)  # fallback to host path
        else:
            runtime_paths.append(result["path"])
    return runtime_paths
