"""
Email handler — orchestrates poll, dispatch, and reply. 

Requires agent context.
"""

import asyncio
import base64
import json
import os
import uuid

from agent import Agent, AgentContext, AgentContextType, UserMessage
from helpers import guids, plugins, files, runtime
from helpers import message_queue as mq
from helpers.persist_chat import save_tmp_chat
from helpers.print_style import PrintStyle
from helpers.errors import format_error
from initialize import initialize_agent

from plugins._email_integration.helpers import dispatcher as disp
from plugins._email_integration.helpers.imap_client import (
    InboundMessage,
    connect_imap,
    disconnect_imap,
    fetch_new,
    fetch_unread_since,
    get_highest_uid,
    connect_exchange,
    fetch_unread_exchange,
)
from plugins._email_integration.helpers.smtp_client import SmtpConfig, send_reply


PLUGIN_NAME = "_email_integration"
DOWNLOAD_FOLDER = "usr/email/attachments"
STATE_FILE = "usr/email/state.json"


# ------------------------------------------------------------------
# UID state persistence
# ------------------------------------------------------------------

_state_lock = asyncio.Lock()

# Poll task registry — lives here (not in extension module) because
# extension modules are re-executed on each job_loop tick (cache disabled),
# which would reset module-level state and orphan running tasks.
_poll_tasks: dict[str, asyncio.Task] = {}  # type: ignore[type-arg]

def _load_state() -> dict:
    path = files.get_abs_path(STATE_FILE)
    if os.path.isfile(path):
        try:
            return json.loads(files.read_file(path))
        except Exception:
            return {}
    return {}


def _save_state(state: dict):
    path = files.get_abs_path(STATE_FILE)
    files.make_dirs(path)
    files.write_file(path, json.dumps(state))


# ------------------------------------------------------------------
# Single handler poll (called from per-handler poll loop)
# ------------------------------------------------------------------

async def _poll_single_handler(handler_cfg: dict, state: dict):
    name = handler_cfg.get("name", "default")
    account_type = handler_cfg.get("account_type", "imap")
    whitelist = handler_cfg.get("sender_whitelist") or []
    last_uid = state.get(name, {}).get("last_uid", 0)
    process_unread_days = int(handler_cfg.get("process_unread_days", 0))

    if account_type == "exchange":
        messages = await _fetch_exchange(handler_cfg, whitelist, process_unread_days)
        if messages:
            await _dispatch_all(handler_cfg, messages)
        return

    client = await connect_imap(
        server=handler_cfg.get("imap_server", ""),
        port=int(handler_cfg.get("imap_port", 993)),
        username=handler_cfg.get("username", ""),
        password=handler_cfg.get("password", ""),
    )
    try:
        # First run: optionally process unread from last N days
        if last_uid == 0:
            if process_unread_days > 0:
                messages, highest = await fetch_unread_since(
                    client, DOWNLOAD_FOLDER, process_unread_days, whitelist or None,
                )
                highest = highest or await get_highest_uid(client)
                state[name] = {"last_uid": highest}
                if messages:
                    PrintStyle.info(
                        f"Email ({name}): processing {len(messages)} unread"
                        f" from last {process_unread_days} days"
                    )
                    await _dispatch_all(handler_cfg, messages)
                else:
                    PrintStyle.info(
                        f"Email ({name}): no unread in last {process_unread_days} days"
                    )
            else:
                highest = await get_highest_uid(client)
                state[name] = {"last_uid": highest}
                PrintStyle.info(f"Email ({name}): initialized, tracking from UID {highest}")
            return

        messages, new_uid = await fetch_new(
            client, DOWNLOAD_FOLDER, last_uid, whitelist or None,
        )

        if new_uid > last_uid:
            state[name] = {"last_uid": new_uid}

        if messages:
            PrintStyle.info(f"Email ({name}): {len(messages)} new messages")
            await _dispatch_all(handler_cfg, messages)

    finally:
        await disconnect_imap(client)


async def _fetch_exchange(
    cfg: dict, whitelist: list[str], since_days: int = 0,
) -> list[InboundMessage]:
    account = await connect_exchange(
        server=cfg.get("imap_server", ""),
        username=cfg.get("username", ""),
        password=cfg.get("password", ""),
    )
    return await fetch_unread_exchange(
        account, DOWNLOAD_FOLDER, whitelist or None, since_days=since_days,
    )


async def _dispatch_all(handler_cfg: dict, messages: list[InboundMessage]):
    own_address = (handler_cfg.get("username") or "").lower()

    # Need an agent for dispatcher AI calls 
    # find existing dispatcher or create new background context
    ctx = None
    for c in AgentContext._contexts.values():
        if isinstance(c, AgentContext) and c.name == "Email Dispatcher":
            ctx = c
            break

    if not ctx:
        agent_config = initialize_agent()
        ctx = AgentContext(agent_config, name="Email Dispatcher",
                           type=AgentContextType.BACKGROUND)
    agent = ctx.agent0

    for msg in messages:
        if own_address and _is_own_email(msg.sender, own_address):
            PrintStyle.info(f"Email: skipping self-sent from {msg.sender}")
            continue
        try:
            await _dispatch_message(agent, handler_cfg, msg)
        except Exception as e:
            PrintStyle.error(f"Email dispatch error: {format_error(e)}")


# ------------------------------------------------------------------
# Dispatch a single inbound message
# ------------------------------------------------------------------

async def _dispatch_message(agent: Agent, handler_cfg: dict, msg: InboundMessage):
    handler_name = handler_cfg.get("name", "default")
    thread_id = disp.extract_thread_id(msg.subject)

    existing = _find_handler_chats(handler_name, msg.sender)

    # Fast path: thread ID in subject matches a known chat
    if thread_id:
        for chat in existing:
            if chat["thread_id"] == thread_id:
                await _route_to_chat(
                    agent, handler_cfg, msg, chat["context_id"],
                )
                return

    # Dispatcher AI decides
    decision = await _call_dispatcher(agent, handler_cfg, msg, existing)
    reason = decision.reason or ""

    if decision.action == "continue_chat" and decision.context_id:
        ctx = AgentContext.get(decision.context_id)
        if ctx:
            await _route_to_chat(agent, handler_cfg, msg, decision.context_id)
            return
        PrintStyle.warning(
            f"Dispatcher referenced unknown context {decision.context_id}, starting new chat"
        )

    await _start_new_chat(agent, handler_cfg, msg)


async def _call_model(
    agent: Agent, handler_cfg: dict, system: str, prompt: str,
):
    if handler_cfg.get("dispatcher_model", "utility") == "chat":
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=system), HumanMessage(content=prompt)]
        response, _ = await agent.call_chat_model(messages)
        return response
    return await agent.call_utility_model(system=system, message=prompt)


async def _call_dispatcher(
    agent: Agent,
    handler_cfg: dict,
    msg: InboundMessage,
    existing_chats: list[disp.ChatSummary],
) -> disp.DispatchDecision:
    body_preview = disp.truncate_body(msg.body)
    chats_text = disp.format_chats_list(existing_chats)

    prompt = agent.read_prompt(
        "fw.email.dispatcher_prompt.md",
        sender=msg.sender,
        subject=msg.subject,
        body=body_preview,
        chats=chats_text,
    )

    extra = handler_cfg.get("dispatcher_instructions", "")
    if extra:
        prompt += agent.read_prompt(
            "fw.email.dispatcher_extra.md", instructions=extra,
        )

    system = agent.read_prompt("fw.email.dispatcher_system.md")

    try:
        response = await _call_model(agent, handler_cfg, system, prompt)
        return disp.parse_dispatcher_response(str(response))
        
    except Exception as e:
        PrintStyle.error(f"Dispatcher error: {format_error(e)}")
        return disp.DispatchDecision(action="new_chat", reason="dispatcher error")


# ------------------------------------------------------------------
# Chat creation and routing
# ------------------------------------------------------------------

async def _start_new_chat(agent: Agent, handler_cfg: dict, msg: InboundMessage):
    from helpers import projects

    handler_name = handler_cfg.get("name", "default")
    thread_id = guids.generate_id()

    config = initialize_agent()
    context = AgentContext(config, name=f"Email: {msg.subject[:50]}")

    context.data[disp.CTX_EMAIL_HANDLER] = handler_name
    context.data[disp.CTX_EMAIL_SENDER] = msg.sender
    context.data[disp.CTX_EMAIL_THREAD_ID] = thread_id
    context.data[disp.CTX_EMAIL_SUBJECT] = msg.subject
    context.data[disp.CTX_EMAIL_LAST_BODY] = msg.body
    context.data[disp.CTX_EMAIL_MESSAGE_ID] = msg.message_id
    
    refs_list = []
    if msg.references:
        for r in msg.references.split():
            if r not in refs_list:
                refs_list.append(r)
    if msg.message_id and msg.message_id not in refs_list:
        refs_list.append(msg.message_id)
        
    context.data[disp.CTX_EMAIL_REFERENCES] = " ".join(refs_list)

    project = handler_cfg.get("project", "")
    if project:
        projects.activate_project(context.id, project)

    save_tmp_chat(context)

    user_msg = _build_user_message(agent, msg, handler_cfg)
    system_ctx = agent.read_prompt("fw.email.system_context.md")

    msg_id = str(uuid.uuid4())
    mq.log_user_message(context, user_msg, msg.attachments or [], message_id=msg_id, source=" (email)")
    context.communicate(UserMessage(
        message=user_msg,
        system_message=[system_ctx],
        attachments=msg.attachments,
        id=msg_id,
    ))

    PrintStyle.success(f"Email: new chat {context.id} for '{msg.subject}' from {msg.sender}")


async def _route_to_chat(
    agent: Agent,
    handler_cfg: dict,
    msg: InboundMessage,
    context_id: str,
):
    context = AgentContext.get(context_id)
    if not context:
        return

    context.data[disp.CTX_EMAIL_MESSAGE_ID] = msg.message_id
    context.data[disp.CTX_EMAIL_LAST_BODY] = msg.body
    
    refs = context.data.get(disp.CTX_EMAIL_REFERENCES, "")
    refs_list = refs.split() if refs else []
    
    if msg.references:
        for r in msg.references.split():
            if r not in refs_list:
                refs_list.append(r)
                
    if msg.message_id and msg.message_id not in refs_list:
        refs_list.append(msg.message_id)
        
    context.data[disp.CTX_EMAIL_REFERENCES] = " ".join(refs_list)

    user_msg = _build_user_message(agent, msg, handler_cfg)
    msg_id = str(uuid.uuid4())
    mq.log_user_message(context, user_msg, msg.attachments or [], message_id=msg_id, source=" (email)")
    context.communicate(UserMessage(
        message=user_msg,
        attachments=msg.attachments,
        id=msg_id,
    ))

    save_tmp_chat(context)
    PrintStyle.info(f"Email: continuing chat {context_id}")


# ------------------------------------------------------------------
# Chat discovery
# ------------------------------------------------------------------

HISTORY_PREVIEW_MAX_CHARS: int = 500


def _find_handler_chats(handler_name: str, sender: str) -> list[disp.ChatSummary]:
    results = []
    for ctx_id, ctx in AgentContext._contexts.items():
        if not isinstance(ctx, AgentContext):
            continue
        data = ctx.data
        if data.get(disp.CTX_EMAIL_HANDLER) != handler_name:
            continue
        if data.get(disp.CTX_EMAIL_SENDER, "").lower() != sender.lower():
            continue
        summary = disp.build_chat_summary(ctx_id, data)
        summary["history_preview"] = _get_history_preview(ctx)
        results.append(summary)

    results.sort(key=lambda c: c["context_id"], reverse=True)
    return results[:20]


def _get_history_preview(ctx: AgentContext) -> str:
    try:
        history = ctx.agent0.history
        text = history.output_text(human_label="user", ai_label="agent")
        if not text:
            return "(empty)"
        if len(text) > HISTORY_PREVIEW_MAX_CHARS:
            return "..." + text[-HISTORY_PREVIEW_MAX_CHARS:]
        return text
    except Exception:
        return "(unavailable)"


# ------------------------------------------------------------------
# Sender helpers
# ------------------------------------------------------------------

def _is_own_email(sender: str, own_address: str) -> bool:
    sender_lower = sender.lower()
    if "<" in sender_lower:
        start = sender_lower.index("<") + 1
        end = sender_lower.index(">", start)
        return sender_lower[start:end].strip() == own_address
    return sender_lower.strip() == own_address


# ------------------------------------------------------------------
# Message builders
# ------------------------------------------------------------------

def _build_user_message(agent: Agent, msg: InboundMessage, handler_cfg: dict) -> str:
    recipient = handler_cfg.get("username", "")
    return agent.read_prompt(
        "fw.email.user_message.md",
        sender=msg.sender,
        recipient=recipient,
        subject=msg.subject,
        body=msg.body,
    )


# ------------------------------------------------------------------
# Reply sending (called from process_chain_end extension)
# ------------------------------------------------------------------

async def send_email_reply(
    context: AgentContext,
    response_text: str,
    attachments: list[str] | None = None,
) -> str | None:
    handler_name = context.data.get(disp.CTX_EMAIL_HANDLER)
    if not handler_name:
        return "No email handler configured"

    cfg = _get_handler_config(handler_name)
    if not cfg:
        return f"Handler config not found for '{handler_name}'"

    sender = context.data.get(disp.CTX_EMAIL_SENDER, "")
    original_subject = context.data.get(disp.CTX_EMAIL_SUBJECT, "")
    thread_id = context.data.get(disp.CTX_EMAIL_THREAD_ID, "")
    original_msg_id = context.data.get(disp.CTX_EMAIL_MESSAGE_ID, "")
    references = context.data.get(disp.CTX_EMAIL_REFERENCES, "")

    subject = disp.build_reply_subject(original_subject, thread_id)

    smtp_cfg = SmtpConfig(
        server=cfg.get("smtp_server", cfg.get("imap_server", "")),
        port=int(cfg.get("smtp_port", 587)),
        username=cfg.get("username", ""),
        password=cfg.get("password", ""),
    )

    # Read attachment files via RFC (they live in the execution runtime)
    attachment_data = await _read_attachments_via_rfc(attachments)

    last_body = context.data.get(disp.CTX_EMAIL_LAST_BODY, "").strip()
    if last_body:
        quoted = "\n> " + "\n> ".join(last_body.splitlines())
        response_text = f"{response_text}\n\nOn previous message:\n{quoted}"

    return await send_reply(
        config=smtp_cfg,
        to=sender,
        subject=subject,
        body=response_text,
        in_reply_to=original_msg_id,
        references=references,
        attachments=attachment_data or None,
    )


# ------------------------------------------------------------------
# Attachment reading (via RFC into execution runtime)
# ------------------------------------------------------------------

async def _read_attachments_via_rfc(
    paths: list[str] | None,
) -> list[tuple[str, bytes]]:
    if not paths:
        return []

    from plugins._email_integration.helpers.attachment_reader import read_attachment

    results: list[tuple[str, bytes]] = []
    for path in paths:
        data = await runtime.call_development_function(read_attachment, path)
        if data["error"]:
            PrintStyle.error(f"Email attachment: {data['error']}")
            continue
        results.append((data["name"], base64.b64decode(data["content_b64"])))
    return results


# ------------------------------------------------------------------
# Config lookup
# ------------------------------------------------------------------

def _get_handler_config(handler_name: str) -> dict | None:
    config = plugins.get_plugin_config(PLUGIN_NAME) or {}
    handlers = config.get("handlers", [])
    for h in handlers:
        if h.get("name") == handler_name:
            return h
    return None
