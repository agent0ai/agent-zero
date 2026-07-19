from functools import partial
from typing import Any

from helpers.extension import Extension
from helpers.errors import format_error
from helpers.print_style import PrintStyle
from helpers import plugins
from plugins._telegram_integration.helpers.dependencies import ensure_dependencies, has_aiogram


PLUGIN_NAME: str = "_telegram_integration"


class TelegramBotManager(Extension):

    async def execute(self, **kwargs: Any) -> None:
        config = plugins.get_plugin_config(PLUGIN_NAME) or {}
        bots_cfg = config.get("bots", [])
        enabled_names = {
            b["name"] for b in bots_cfg if b.get("enabled") and b.get("name") and b.get("token")
        }

        # Avoid installing aiogram on idle ticks when Telegram is not configured.
        if not enabled_names and not has_aiogram():
            return

        if enabled_names:
            ensure_dependencies()

        from plugins._telegram_integration.helpers.bot_manager import (
            get_all_bots,
            create_bot,
            cache_bot_info,
            start_polling,
            setup_webhook,
            stop_bot,
        )
        from plugins._telegram_integration.helpers.handler import (
            handle_start,
            handle_clear,
            handle_message,
            handle_callback_query,
            handle_new_members,
            cleanup_old_attachments,
        )

        cleanup_old_attachments()

        running = get_all_bots()

        # Stop bots that are no longer enabled
        for name in list(running.keys()):
            if name not in enabled_names:
                await stop_bot(name)

        # Start new bots
        for bot_cfg in bots_cfg:
            name = bot_cfg.get("name", "")
            if not name or not bot_cfg.get("enabled") or not bot_cfg.get("token"):
                continue
            if name in running:
                inst = running[name]
                current_mode = bot_cfg.get("mode", "polling")
                running_mode = "webhook" if inst.webhook_active else "polling"
                current_group_mode = bot_cfg.get("group_mode", "mention")
                if current_mode == running_mode and current_group_mode == inst.group_mode:
                    # Same mode and still alive → skip
                    if (inst.task and not inst.task.done()) or inst.webhook_active:
                        continue
                # Mode changed or instance died — stop and recreate
                await stop_bot(name)

            try:
                # Create handler closures that capture bot_name and config
                _on_start = partial(_make_handler(handle_start), bot_name=name, bot_cfg=bot_cfg)
                _on_clear = partial(_make_handler(handle_clear), bot_name=name, bot_cfg=bot_cfg)
                _on_message = partial(_make_handler(handle_message), bot_name=name, bot_cfg=bot_cfg)
                _on_callback = partial(_make_handler(handle_callback_query), bot_name=name, bot_cfg=bot_cfg)
                _on_new_members = partial(_make_handler(handle_new_members), bot_name=name, bot_cfg=bot_cfg)

                instance = create_bot(
                    name=name,
                    token=bot_cfg["token"],
                    on_message=_on_message,
                    on_command_start=_on_start,
                    on_command_clear=_on_clear,
                    on_command_control=_on_message,
                    on_callback_query=_on_callback,
                    on_new_members=_on_new_members,
                    group_mode=bot_cfg.get("group_mode", "mention"),
                )

                await cache_bot_info(instance)

                mode = bot_cfg.get("mode", "polling")
                if mode == "webhook":
                    webhook_url = bot_cfg.get("webhook_url", "")
                    webhook_secret = bot_cfg.get("webhook_secret", "")
                    if webhook_url:
                        await setup_webhook(instance, webhook_url, webhook_secret)
                    else:
                        PrintStyle.error(
                            f"Telegram ({name}): webhook mode requires webhook_url"
                        )
                        continue
                else:
                    await start_polling(instance)

                PrintStyle.success(f"Telegram ({name}): bot started in {mode} mode")

            except Exception as e:
                PrintStyle.error(
                    f"Telegram ({name}): failed to start: {format_error(e)}"
                )

# Wrapper functions for aiogram handlers

def _get_current_bot_cfg(bot_name: str) -> dict:
    """Fetch the latest bot config by name, so handlers always use fresh settings."""
    config = plugins.get_plugin_config(PLUGIN_NAME) or {}
    for b in config.get("bots", []):
        if b.get("name") == bot_name:
            return b
    return {}


def _make_handler(handler_fn):
    """Create a wrapper that resolves fresh bot config on every call."""
    async def _wrapped(event, bot_name: str, bot_cfg: dict):
        await handler_fn(event, bot_name, _get_current_bot_cfg(bot_name) or bot_cfg)
    return _wrapped
