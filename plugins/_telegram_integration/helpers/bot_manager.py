import asyncio
import re
from dataclasses import dataclass, field
from typing import Callable, Awaitable

from plugins._telegram_integration.helpers.sandbox import Bot, TelegramEvent, worker, decode, rpc
from helpers import integration_commands

from helpers.errors import format_error
from helpers.print_style import PrintStyle

# Data models

@dataclass
class BotInstance:
    name: str
    bot: Bot
    handlers: dict
    task: asyncio.Task | None = None  # polling task
    webhook_active: bool = False  # True when webhook mode is registered
    webhook_secret: str = ""  # secret for webhook verification
    webhook_url: str = ""
    group_mode: str = "mention"  # current group_mode setting
    generation: int = 0
    deliveries: set = field(default_factory=set)
    bot_info: object | None = None  # cached result of bot.get_me()

# Bot registry (singleton, persists across module reloads)

_bots: dict[str, BotInstance] = {}


def get_bot(name: str) -> BotInstance | None:
    return _bots.get(name)


def get_all_bots() -> dict[str, BotInstance]:
    return _bots

# Bot creation

def create_bot(
    name: str,
    token: str,
    on_message: Callable[..., Awaitable],
    on_command_start: Callable[..., Awaitable],
    on_command_control: Callable[..., Awaitable] | None = None,
    on_callback_query: Callable[..., Awaitable] | None = None,
    on_new_members: Callable[..., Awaitable] | None = None,
    group_mode: str = "mention",
) -> BotInstance:
    bot = Bot(token, parse_mode='HTML')
    instance = BotInstance(name=name, bot=bot, group_mode=group_mode, handlers={
        'message': on_message, 'start': on_command_start, 'control': on_command_control,
        'callback': on_callback_query, 'members': on_new_members,
    })
    _bots[name] = instance
    return instance


async def register_bot_commands(instance: BotInstance) -> None:
    """Register native integration and globally available Agent Zero commands."""
    from plugins._telegram_integration.helpers.slash_commands import menu_commands

    commands = [
        dict(command=name, description=description)
        for name, description in menu_commands()
    ]
    if not commands:
        return
    try:
        await instance.bot.set_my_commands(commands=commands)
        PrintStyle.info(f"Telegram ({instance.name}): registered {len(commands)} bot commands")
    except Exception as e:
        PrintStyle.error(f"Telegram ({instance.name}): failed to register bot commands: {format_error(e)}")


async def cache_bot_info(instance: BotInstance):
    """Fetch and cache bot info. Call after create_bot."""
    await worker.aprepare()
    if not instance.bot_info or instance.generation != worker.generation:
        info = await rpc({'action': 'create', 'name': instance.name, 'token': instance.bot.token,
                                   'group_mode': instance.group_mode,
                                   'commands': integration_commands.command_names(integration='telegram')})
        instance.bot_info = decode(info, instance.bot)
        instance.generation = worker.generation
    return instance.bot_info


async def dispatch_events(instance, events, *, wait=False):
    deliveries = []
    for event in events:
        handler = instance.handlers.get(event['kind'])
        if handler:
            task = asyncio.create_task(handler(TelegramEvent(event['event'], instance.bot)))
            instance.deliveries.add(task)
            deliveries.append(task)
            def finished(task):
                instance.deliveries.discard(task)
                if not task.cancelled() and task.exception():
                    PrintStyle.error(f'Telegram delivery failed ({type(task.exception()).__name__})')
            task.add_done_callback(finished)
    if wait:
        await asyncio.gather(*deliveries)


async def feed_webhook(instance, update):
    await cache_bot_info(instance)
    events = await rpc({'action': 'webhook', 'name': instance.name, 'update': update})
    await dispatch_events(instance, events, wait=True)


async def start_polling(instance):
    await remove_webhook(instance)
    await cache_bot_info(instance)
    await rpc({'action': 'start_polling', 'name': instance.name})
    async def poll():
        while True:
            events = await rpc({'action': 'events', 'name': instance.name})
            await dispatch_events(instance, events)
            await asyncio.sleep(.25)
    instance.task = asyncio.create_task(poll())
    return instance.task


async def stop_polling(instance):
    if instance.task and not instance.task.done():
        instance.task.cancel()
        await asyncio.gather(instance.task, return_exceptions=True)
    instance.task = None

# Webhook

async def setup_webhook(instance: BotInstance, webhook_url: str, secret: str = ""):
    """Register webhook with Telegram. Updates are received via the API handler."""
    if not isinstance(secret, str) or not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", secret):
        raise ValueError("webhook_secret must contain 32–256 letters, digits, underscores or hyphens")

    full_url = f"{webhook_url.rstrip('/')}/api/plugins/_telegram_integration/webhook?bot={instance.name}"

    await instance.bot.set_webhook(
        url=full_url,
        secret_token=secret,
    )

    instance.webhook_active = True
    instance.webhook_secret = secret
    instance.webhook_url = webhook_url.rstrip("/")
    PrintStyle.info(f"Telegram ({instance.name}): webhook active via {webhook_url.rstrip('/')}")


async def remove_webhook(instance: BotInstance):
    instance.webhook_active = False
    instance.webhook_secret = ""
    instance.webhook_url = ""
    try:
        await instance.bot.delete_webhook()
    except Exception as e:
        PrintStyle.error(f"Telegram ({instance.name}): remove webhook error: {format_error(e)}")

# Cleanup

async def stop_bot(name: str):
    instance = _bots.pop(name, None)
    if not instance:
        return
    for task in list(instance.deliveries):
        task.cancel()
    await asyncio.gather(*instance.deliveries, return_exceptions=True)
    if instance.task and not instance.task.done():
        await stop_polling(instance)
    else:
        await remove_webhook(instance)
    try:
        if worker.ready:
            await rpc({'action': 'stop', 'name': name})
        if not _bots:
            await asyncio.to_thread(worker.stop)
        await instance.bot.session.close()
    except Exception:
        pass
    PrintStyle.info(f"Telegram ({name}): stopped")


# Test connection

async def test_token(token: str) -> tuple[bool, str]:
    try:
        bot = Bot(token=token)
        info = await bot.get_me()
        await bot.session.close()
        return True, f"Connected as @{info.username} ({info.first_name})"
    except Exception as e:
        return False, format_error(e)
