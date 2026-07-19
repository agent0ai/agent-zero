from __future__ import annotations

import asyncio
import re
import time
from contextlib import suppress

from agent import AgentContext
from helpers.print_style import PrintStyle
from plugins._telegram_integration.helpers import telegram_client as tc
from plugins._telegram_integration.helpers.bot_manager import get_bot
from plugins._telegram_integration.helpers.constants import (
    CTX_TG_BOT,
    CTX_TG_CHAT_ID,
    CTX_TG_HEARTBEAT_STOP,
    CTX_TG_HEARTBEAT_TASK,
)


HEARTBEAT_INTERVAL_SECONDS = 180


async def start(context: AgentContext) -> None:
    task = context.data.get(CTX_TG_HEARTBEAT_TASK)
    if task and not task.done():
        return

    stop_event = asyncio.Event()
    context.data[CTX_TG_HEARTBEAT_STOP] = stop_event
    context.data[CTX_TG_HEARTBEAT_TASK] = asyncio.create_task(
        _heartbeat_loop(context, stop_event, time.monotonic())
    )


async def stop(context: AgentContext) -> None:
    stop_event = context.data.pop(CTX_TG_HEARTBEAT_STOP, None)
    if stop_event:
        stop_event.set()

    task = context.data.pop(CTX_TG_HEARTBEAT_TASK, None)
    if task and not task.done():
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


async def _heartbeat_loop(
    context: AgentContext,
    stop_event: asyncio.Event,
    started_at: float,
) -> None:
    try:
        while True:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=HEARTBEAT_INTERVAL_SECONDS)
                return
            except asyncio.TimeoutError:
                await _send_heartbeat(context, time.monotonic() - started_at)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        PrintStyle.debug(f"Telegram heartbeat stopped: {exc}")


async def _send_heartbeat(context: AgentContext, elapsed_seconds: float) -> bool:
    bot_name = context.data.get(CTX_TG_BOT)
    chat_id = context.data.get(CTX_TG_CHAT_ID)
    bot = get_bot(bot_name) if bot_name else None
    if not bot or not chat_id:
        return False

    text = heartbeat_text(elapsed_seconds, _current_reason(context))
    sent_id = await tc.raw_send_text(
        bot.bot.token,
        int(chat_id),
        text,
        parse_mode=None,
    )
    return bool(sent_id)


def heartbeat_text(elapsed_seconds: float, reason: str = "") -> str:
    minutes = max(1, int(round(elapsed_seconds / 60)))
    detail = reason or "working on your request"
    return f"Still working... ({minutes} min elapsed - {detail})"


def _current_reason(context: AgentContext) -> str:
    progress = str(getattr(getattr(context, "log", None), "progress", "") or "")
    progress = _clean_progress(progress)
    if not progress or progress.lower() == "waiting for input":
        return "working on your request"
    return progress


def _clean_progress(text: str) -> str:
    value = re.sub(r"icon://[a-zA-Z0-9_]+(?:\[[^\]]*\])?\s*", "", text)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > 80:
        value = f"{value[:77].rstrip()}..."
    return value
