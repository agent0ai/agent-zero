from functools import partial
from typing import Any

from helpers.extension import Extension
from helpers.errors import format_error
from helpers.print_style import PrintStyle
from helpers.notification import NotificationManager, NotificationPriority, NotificationType
from plugins._telegram_integration.helpers.dependencies import ensure_dependencies, has_aiogram
from plugins._telegram_integration.helpers import scopes


class TelegramBotManager(Extension):

    async def execute(self, **kwargs: Any) -> None:
        try:
            from plugins._telegram_integration.helpers.migration import prepare_upgrade
            prepare_upgrade()
            configured, conflicts = scopes.available_bots()
        except Exception:
            configured, conflicts = {}, ["Unreadable Telegram configuration"]
        if conflicts:
            NotificationManager.send_notification(
                type=NotificationType.ERROR,
                priority=NotificationPriority.HIGH,
                title="Telegram settings need review",
                message=(
                    "Conflicting or unreadable Telegram settings were found. Each configured scope "
                    "needs a separate bot token from @BotFather. Affected bots are paused; "
                    "existing settings are retained. Review the saved configurations and the "
                    "upgrade backup under usr/plugins/_telegram_integration/backups/config-scopes-v1."
                ),
                id="telegram-scope-conflicts",
            )
        enabled_names = set(configured)

        # Avoid installing aiogram on idle ticks when Telegram is not configured.
        if not enabled_names and not has_aiogram():
            return

        if enabled_names:
            ensure_dependencies()

        from plugins._telegram_integration.helpers.bot_manager import (
            get_all_bots,
            create_bot,
            cache_bot_info,
            register_bot_commands,
            start_polling,
            setup_webhook,
            stop_bot,
        )
        from plugins._telegram_integration.helpers.handler import (
            handle_start,
            handle_message,
            handle_callback_query,
            handle_new_members,
            cleanup_old_attachments,
        )

        if configured:
            cleanup_old_attachments({key: bot.config for key, bot in configured.items()})

        running = get_all_bots()

        # Stop bots that are no longer enabled
        for name in list(running.keys()):
            if name not in enabled_names:
                await stop_bot(name)

        # Start new bots
        for name, scoped_bot in configured.items():
            bot_cfg = scoped_bot.config
            if name in running:
                inst = running[name]
                current_mode = bot_cfg.get("mode", "polling")
                running_mode = "webhook" if inst.webhook_active else "polling"
                current_group_mode = bot_cfg.get("group_mode", "mention")
                same_connection = (
                    bot_cfg["token"] == inst.bot.token
                    and (current_mode != "webhook" or (
                        bot_cfg.get("webhook_url", "").rstrip("/") == inst.webhook_url
                        and bot_cfg.get("webhook_secret", "") == inst.webhook_secret
                    ))
                )
                if current_mode == running_mode and current_group_mode == inst.group_mode and same_connection:
                    # Same mode and still alive → skip
                    if (inst.task and not inst.task.done()) or inst.webhook_active:
                        continue
                # Mode changed or instance died — stop and recreate
                await stop_bot(name)

            try:
                # Create handler closures that capture bot_name and config
                _on_start = partial(_make_handler(handle_start), bot_name=name, bot_cfg=bot_cfg)
                _on_message = partial(_make_handler(handle_message), bot_name=name, bot_cfg=bot_cfg)
                _on_callback = partial(_make_handler(handle_callback_query), bot_name=name, bot_cfg=bot_cfg)
                _on_new_members = partial(_make_handler(handle_new_members), bot_name=name, bot_cfg=bot_cfg)

                instance = create_bot(
                    name=name,
                    token=bot_cfg["token"],
                    on_message=_on_message,
                    on_command_start=_on_start,
                    on_command_control=_on_message,
                    on_callback_query=_on_callback,
                    on_new_members=_on_new_members,
                    group_mode=bot_cfg.get("group_mode", "mention"),
                )

                await cache_bot_info(instance)
                await register_bot_commands(instance)

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

def _get_current_bot_cfg(bot_name: str, event, captured: dict) -> dict:
    from plugins._telegram_integration.helpers import handler
    bots, _ = scopes.available_bots()
    bot = bots.get(bot_name)
    if not bot:
        return {}
    mode = bot.config.get("mode", "polling")
    if bot.config["token"] != captured.get("token") or mode != captured.get("mode", "polling"):
        return {}
    if mode == "webhook" and (
        bot.config.get("webhook_url", "").rstrip("/") != captured.get("webhook_url", "").rstrip("/")
        or bot.config.get("webhook_secret", "") != captured.get("webhook_secret", "")
    ):
        return {}
    user = event.from_user
    message = getattr(event, "message", None) or event
    if not user or not getattr(message, "chat", None):
        return {}
    context = handler.get_bound_context(bot_name, user.id, message.chat.id)
    if context:
        project = handler.projects.get_context_project_name(context) or ""
        profile = context.config.profile
    else:
        project, profile = scopes.initial_scope(bot, user.id)
    config = scopes.resolve(bot, project, profile)
    if not config or not handler._is_allowed(config, user.id, user.username):
        return {}
    if config.get("group_mode") == "off" and message.chat.type != "private":
        return {}
    return {**config, "_initial_scope": (project, profile)}


def _make_handler(handler_fn):
    """Create a wrapper that resolves fresh bot config on every call."""
    async def _wrapped(event, bot_name: str, bot_cfg: dict):
        try:
            current = _get_current_bot_cfg(bot_name, event, bot_cfg)
        except Exception:
            PrintStyle.error("Telegram: could not resolve current access rules; update rejected")
            return
        if current:
            message = getattr(event, "message", None) or event
            if (handler_fn.__name__ == "handle_message" and current.get("group_mode", "mention") == "mention"
                    and message.chat.type != "private" and not (message.text or message.caption or "").startswith("/")):
                from plugins._telegram_integration.helpers.bot_manager import get_bot, _make_group_mention_filter
                instance = get_bot(bot_name)
                if instance:
                    await _make_group_mention_filter(partial(handler_fn, bot_name=bot_name, bot_cfg=current), instance.bot)(event)
                return
            await handler_fn(event, bot_name, current)
    return _wrapped
