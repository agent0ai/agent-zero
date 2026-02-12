import asyncio
import threading
from typing import Optional

from python.helpers.print_style import PrintStyle
from python.helpers import settings
from python.helpers.secrets import get_default_secrets_manager

_PRINTER = PrintStyle(italic=True, font_color="#0088cc", padding=False)

TELEGRAM_MESSAGE_TIMEOUT = 300

_bot_app = None
_bot_thread: Optional[threading.Thread] = None
_bot_lock = threading.Lock()
_chat_contexts_lock: Optional[asyncio.Lock] = None
_chat_contexts: dict[int, str] = {}
_bot_shutdown = False


def _get_chat_contexts_lock() -> asyncio.Lock:
    global _chat_contexts_lock
    if _chat_contexts_lock is None:
        _chat_contexts_lock = asyncio.Lock()
    return _chat_contexts_lock


def _get_allowed_users() -> set[int]:
    secrets_manager = get_default_secrets_manager()
    secrets = secrets_manager.load_secrets()
    raw = secrets.get("TELEGRAM_BOT_ALLOWED_USERS", "")
    if not raw or not raw.strip():
        return set()
    result = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            result.add(int(part))
    return result


async def _handle_message(update, context) -> None:
    from agent import AgentContext, UserMessage
    from initialize import initialize_agent

    if update.message is None:
        return

    telegram_chat_id = update.effective_chat.id
    telegram_user_id = update.effective_user.id if update.effective_user else None

    allowed = _get_allowed_users()
    if allowed and telegram_user_id not in allowed:
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    user_text = update.message.text or ""
    if not user_text.strip():
        await update.message.reply_text("Please send a text message.")
        return

    _PRINTER.print(f"Telegram message from user {telegram_user_id} in chat {telegram_chat_id}")

    lock = _get_chat_contexts_lock()
    async with lock:
        agent_context = None
        ctx_id = _chat_contexts.get(telegram_chat_id)
        if ctx_id:
            agent_context = AgentContext.get(ctx_id)

        if agent_context is None:
            config = initialize_agent()
            from agent import AgentContextType

            agent_context = AgentContext.first()
            if not agent_context:
                agent_context = AgentContext(config=config, type=AgentContextType.USER)
            _chat_contexts[telegram_chat_id] = agent_context.id
            _PRINTER.print(f"Using context {agent_context.id} for Telegram chat {telegram_chat_id}")

    thinking_msg = await update.message.reply_text("⏳ Processing...")

    try:
        task = agent_context.communicate(
            UserMessage(message=user_text, system_message=[], attachments=[])
        )
        result = await asyncio.wait_for(task.result(), timeout=TELEGRAM_MESSAGE_TIMEOUT)

        response_text = str(result) if result else "⚠️ No response received."
        await _send_long_message(update.effective_chat.id, response_text, context)

    except asyncio.TimeoutError:
        _PRINTER.print(f"Telegram message processing timed out for chat {telegram_chat_id}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⏱️ Request timed out. The agent took too long to respond. Please try a simpler question or try again later.",
        )
    except Exception as e:
        _PRINTER.print(f"Telegram message processing failed: {e}")
        error_msg = "❌ Sorry, I encountered an error processing your message. Please try again."
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=error_msg,
        )
    finally:
        try:
            await thinking_msg.delete()
        except Exception as e:
            _PRINTER.print(f"Failed to delete thinking message: {e}")


async def _handle_start(update, context) -> None:
    allowed = _get_allowed_users()
    telegram_user_id = update.effective_user.id if update.effective_user else None

    if allowed and telegram_user_id not in allowed:
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    await update.message.reply_text(
        "👋 Welcome to Agent Zero!\n\n"
        "Send me any message and I will process it through Agent Zero.\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/new - Start a new conversation\n"
        "/id - Show your Telegram user ID"
    )


async def _handle_new(update, context) -> None:
    allowed = _get_allowed_users()
    telegram_user_id = update.effective_user.id if update.effective_user else None

    if allowed and telegram_user_id not in allowed:
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    telegram_chat_id = update.effective_chat.id

    old_ctx_id = _chat_contexts.pop(telegram_chat_id, None)
    if old_ctx_id:
        from agent import AgentContext
        from python.helpers.persist_chat import remove_chat

        old_ctx = AgentContext.get(old_ctx_id)
        if old_ctx:
            old_ctx.reset()
            AgentContext.remove(old_ctx_id)
            try:
                remove_chat(old_ctx_id)
            except Exception as e:
                _PRINTER.print(f"Failed to remove chat {old_ctx_id}: {e}")

    await update.message.reply_text("🔄 New conversation started. Send me a message!")


async def _handle_id(update, context) -> None:
    user_id = update.effective_user.id if update.effective_user else "unknown"
    await update.message.reply_text(f"Your Telegram user ID: `{user_id}`", parse_mode="Markdown")


async def _send_long_message(chat_id: int, text: str, context, max_length: int = 4096) -> None:
    if len(text) <= max_length:
        await context.bot.send_message(chat_id=chat_id, text=text)
        return

    while text:
        if len(text) <= max_length:
            await context.bot.send_message(chat_id=chat_id, text=text)
            break

        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length

        chunk = text[:split_at]
        text = text[split_at:]
        if text.startswith("\n"):
            text = text[1:]
        await context.bot.send_message(chat_id=chat_id, text=chunk)


async def _run_polling_async() -> None:
    global _bot_shutdown, _bot_app
    _bot_shutdown = False
    try:
        await _bot_app.initialize()
        await _bot_app.start()
        await _bot_app.updater.start_polling(drop_pending_updates=True)
        _PRINTER.print("Telegram bot polling started successfully")
        while not _bot_shutdown:
            await asyncio.sleep(0.5)
    except Exception as e:
        _PRINTER.print(f"Telegram bot error: {e}")
    finally:
        try:
            await _bot_app.updater.stop()
            await _bot_app.stop()
            await _bot_app.shutdown()
        except Exception:
            pass


def _run_bot(token: str) -> None:
    from telegram import BotCommand
    from telegram.ext import Application, MessageHandler, CommandHandler, filters

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    global _bot_app
    _bot_app = Application.builder().token(token).build()

    commands = [
        BotCommand("start", "Show welcome message and available commands"),
        BotCommand("new", "Start a fresh conversation"),
        BotCommand("id", "Show your Telegram user ID"),
    ]
    loop.run_until_complete(_bot_app.bot.set_my_commands(commands))
    _PRINTER.print("Registered bot commands for slash menu")

    _bot_app.add_handler(CommandHandler("start", _handle_start))
    _bot_app.add_handler(CommandHandler("new", _handle_new))
    _bot_app.add_handler(CommandHandler("id", _handle_id))
    _bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_message))

    _PRINTER.print("Starting Telegram bot...")
    loop.run_until_complete(_run_polling_async())


def _stop_bot() -> None:
    global _bot_shutdown, _bot_app, _bot_thread
    _bot_shutdown = True
    if _bot_thread is not None:
        _bot_thread.join(timeout=10)
        _bot_thread = None
    _bot_app = None


def reconfigure_bot() -> None:
    global _bot_thread

    cfg = settings.get_settings()
    enabled = cfg.get("telegram_bot_enabled", False)

    secrets_manager = get_default_secrets_manager()
    secrets = secrets_manager.load_secrets()
    token = secrets.get("TELEGRAM_BOT_TOKEN", "")

    with _bot_lock:
        _stop_bot()

        if not enabled or not token:
            if not enabled:
                _PRINTER.print("Telegram bot is disabled in settings.")
            elif not token:
                _PRINTER.print("Telegram bot token is not configured in secrets.")
            return

        _PRINTER.print("Starting Telegram bot...")
        _bot_thread = threading.Thread(target=_run_bot, args=(token,), daemon=True)
        _bot_thread.start()


def initialize_telegram_bot() -> None:
    cfg = settings.get_settings()
    secrets_manager = get_default_secrets_manager()
    secrets = secrets_manager.load_secrets()
    token = secrets.get("TELEGRAM_BOT_TOKEN", "")

    if cfg.get("telegram_bot_enabled", False) and token:
        reconfigure_bot()
    else:
        _PRINTER.print("Telegram bot is not enabled or token is missing in secrets, skipping initialization.")
