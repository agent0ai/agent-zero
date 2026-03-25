"""
WhatsApp handler — orchestrates poll, dispatch, and reply.

Requires agent context.
"""

import asyncio
import uuid

from agent import Agent, AgentContext, UserMessage
from helpers import plugins
from helpers import message_queue as mq
from helpers.persist_chat import save_tmp_chat
from helpers.print_style import PrintStyle
from helpers.errors import format_error
from initialize import initialize_agent

from plugins._whatsapp_integration.helpers import wa_client
from plugins._whatsapp_integration.helpers import bridge_manager


PLUGIN_NAME = "_whatsapp_integration"
MEDIA_FOLDER = "usr/whatsapp/media"

# Context data keys (no underscore prefix — must persist across restarts)
CTX_WA_CHAT_ID = "wa_chat_id"
CTX_WA_SENDER_NAME = "wa_sender_name"
CTX_WA_SENDER_NUMBER = "wa_sender_number"
CTX_WA_IS_GROUP = "wa_is_group"
CTX_WA_LAST_BODY = "wa_last_body"
# Transient — consumed per-reply, not persisted
CTX_WA_ATTACHMENTS = "_wa_response_attachments"

# Poll task — lives here (not in extension module) because
# extension modules are re-executed on each job_loop tick,
# which would reset module-level state and orphan running tasks.
_poll_task: asyncio.Task | None = None  # type: ignore[type-arg]


# ------------------------------------------------------------------
# Poll loop
# ------------------------------------------------------------------

async def poll_messages(config: dict) -> None:
    port = int(config.get("bridge_port", 3100))
    base_url = bridge_manager.get_bridge_url(port)

    try:
        messages = await wa_client.get_messages(base_url)
    except Exception as e:
        PrintStyle.error(f"WhatsApp poll error: {format_error(e)}")
        return

    if not messages:
        return

    for msg in messages:
        try:
            await _dispatch_message(config, msg)
        except Exception as e:
            PrintStyle.error(f"WhatsApp dispatch error: {format_error(e)}")


# ------------------------------------------------------------------
# Dispatch a single inbound message
# ------------------------------------------------------------------

async def _dispatch_message(config: dict, msg: dict) -> None:
    chat_id = msg.get("chatId", "")

    # Show typing indicator immediately so user sees activity
    port = int(config.get("bridge_port", 3100))
    base_url = bridge_manager.get_bridge_url(port)
    await wa_client.send_typing(base_url, chat_id)

    existing = _find_chats_by_jid(chat_id)

    if existing:
        # Continue most recent chat for this JID
        await _route_to_chat(config, msg, existing[0])
    else:
        await _start_new_chat(config, msg)


# ------------------------------------------------------------------
# Chat creation and routing
# ------------------------------------------------------------------

async def _start_new_chat(config: dict, msg: dict) -> None:
    from helpers import projects

    sender_name = msg.get("senderName", "Unknown")
    sender_number = msg.get("senderId", "").replace("@s.whatsapp.net", "").replace("@lid", "")
    chat_id = msg.get("chatId", "")
    is_group = msg.get("isGroup", False)

    agent_config = initialize_agent()
    context = AgentContext(agent_config, name=f"WhatsApp: {sender_name[:50]}")

    context.data[CTX_WA_CHAT_ID] = chat_id
    context.data[CTX_WA_SENDER_NAME] = sender_name
    context.data[CTX_WA_SENDER_NUMBER] = sender_number
    context.data[CTX_WA_IS_GROUP] = is_group
    context.data[CTX_WA_LAST_BODY] = msg.get("body", "")

    project = config.get("project", "")
    if project:
        projects.activate_project(context.id, project)

    save_tmp_chat(context)

    user_msg = _build_user_message(context.agent0, msg, config)
    system_ctx = context.agent0.read_prompt("fw.wa.system_context.md")

    msg_id = str(uuid.uuid4())
    attachments = msg.get("mediaUrls", [])
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
    config: dict, msg: dict, context_id: str,
) -> None:
    context = AgentContext.get(context_id)
    if not context:
        return

    context.data[CTX_WA_LAST_BODY] = msg.get("body", "")

    user_msg = _build_user_message(context.agent0, msg, config)
    msg_id = str(uuid.uuid4())
    attachments = msg.get("mediaUrls", [])
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
# Message builders
# ------------------------------------------------------------------

def _build_user_message(agent: Agent, msg: dict, config: dict) -> str:
    sender_name = msg.get("senderName", "Unknown")
    sender_number = msg.get("senderId", "").replace("@s.whatsapp.net", "").replace("@lid", "")
    text = agent.read_prompt(
        "fw.wa.user_message.md",
        sender_name=sender_name,
        sender_number=sender_number,
        body=msg.get("body", ""),
    )
    instructions = config.get("agent_instructions", "")
    if instructions:
        text += agent.read_prompt(
            "fw.wa.user_message_instructions.md", instructions=instructions,
        )
    return text


# ------------------------------------------------------------------
# Reply sending (called from process_chain_end extension)
# ------------------------------------------------------------------

async def send_wa_reply(
    context: AgentContext,
    response_text: str,
    attachments: list[str] | None = None,
) -> str | None:
    chat_id = context.data.get(CTX_WA_CHAT_ID)
    if not chat_id:
        return "No WhatsApp chat ID"

    config = plugins.get_plugin_config(PLUGIN_NAME) or {}
    port = int(config.get("bridge_port", 3100))
    base_url = bridge_manager.get_bridge_url(port)

    # Typing indicator
    await wa_client.send_typing(base_url, chat_id)

    # Send text
    try:
        result = await wa_client.send_message(base_url, chat_id, response_text)
        if result.get("error"):
            return result["error"]
    except Exception as e:
        return str(e)

    # Send attachments
    if attachments:
        for file_path in attachments:
            try:
                result = await wa_client.send_media(
                    base_url, chat_id, file_path,
                )
                if result.get("error"):
                    PrintStyle.warning(f"WhatsApp: attachment error: {result['error']}")
            except Exception as e:
                PrintStyle.warning(f"WhatsApp: attachment error: {e}")

    return None
