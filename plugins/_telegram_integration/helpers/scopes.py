"""Resolve Telegram connection ownership and current scoped access rules."""
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from pathlib import Path

from helpers import plugins, projects, settings
from plugins._telegram_integration.helpers.constants import (
    PLUGIN_NAME, CTX_TG_BOT, CTX_TG_BOT_CFG, CTX_TG_CHAT_ID,
    CTX_TG_CHAT_TYPE, CTX_TG_USER_ID, CTX_TG_USERNAME,
)


@dataclass(frozen=True)
class BotConfig:
    project: str
    profile: str
    config: dict

    @property
    def key(self) -> str:
        name = self.config["name"]
        if not self.project and not self.profile:
            return name
        scope = json.dumps([self.project, self.profile]).encode()
        return f"{name}@{sha256(scope).hexdigest()[:24]}"


def configured_bots() -> list[BotConfig]:
    scopes = [("", "")]
    for entry in plugins.find_plugin_assets(plugins.CONFIG_FILE_NAME, plugin_name=PLUGIN_NAME):
        scope = (entry["project_name"], entry["agent_profile"])
        if scope not in scopes:
            scopes.append(scope)
    result = []
    for project, profile in scopes:
        config = plugins.get_plugin_config(PLUGIN_NAME, project_name=project, agent_profile=profile) or {}
        for bot in config.get("bots", []):
            if bot.get("name") and bot.get("token"):
                result.append(BotConfig(project, profile, bot))
    return result


def bot_identity(config: dict) -> str:
    # Token rotation must not create two connections to the same Telegram bot.
    return config["token"].split(":", 1)[0]


def is_safe_name(name) -> bool:
    return isinstance(name, str) and bool(re.fullmatch(r"[^/\\\x00-\x1f\x7f]{1,128}", name))


def enabled(project: str, profile: str) -> bool:
    toggles = plugins.find_plugin_assets(
        plugins.TOGGLE_FILE_PATTERN, plugin_name=PLUGIN_NAME,
        project_name=project, agent_profile=profile,
    )
    return not toggles or Path(toggles[0]["path"]).name == plugins.ENABLED_FILE_NAME


def available_bots() -> tuple[dict[str, BotConfig], list[str]]:
    bots = configured_bots()
    identities = [bot_identity(bot.config) for bot in bots]
    keys = [bot.key for bot in bots]
    conflicts = [bot.key for bot in bots if identities.count(bot_identity(bot.config)) > 1
                 or keys.count(bot.key) > 1 or not is_safe_name(bot.config["name"])]
    toggle_scopes = [(entry["project_name"], entry["agent_profile"])
                     for entry in plugins.find_plugin_assets(plugins.TOGGLE_FILE_PATTERN, plugin_name=PLUGIN_NAME)]
    return {
        bot.key: bot for bot in bots
        if bot.key not in conflicts and bot.config.get("enabled")
        and any(resolve(bot, project or bot.project, profile or bot.profile)
                for project, profile in [(bot.project, bot.profile), *toggle_scopes])
    }, conflicts


def resolve(bot: BotConfig, project: str, profile: str) -> dict:
    if (bot.project and bot.project != project) or (bot.profile and bot.profile != profile):
        return {}
    if not enabled(project, profile):
        return {}
    config = plugins.get_plugin_config(PLUGIN_NAME, project_name=project, agent_profile=profile) or {}
    return next((item for item in config.get("bots", [])
                 if item.get("name") == bot.config["name"]
                 and item.get("token") == bot.config["token"] and item.get("enabled")), {})


def initial_scope(bot: BotConfig, user_id: int) -> tuple[str, str]:
    project = bot.project or (bot.config.get("user_projects") or {}).get(str(user_id)) or bot.config.get("default_project", "")
    profile = bot.profile or settings.get_settings()["agent_profile"]
    return project, profile


def context_config(context, *, project=None, profile=None) -> dict:
    bots, _ = available_bots()
    bot = bots.get(context.data.get(CTX_TG_BOT))
    if not bot:
        return {}
    project = projects.get_context_project_name(context) if project is None else project
    profile = context.config.profile if profile is None else profile
    config = resolve(bot, project or "", profile)
    from plugins._telegram_integration.helpers.handler import _is_allowed
    if (not config or context.data.get(CTX_TG_USER_ID) is None
            or not _is_allowed(config, context.data.get(CTX_TG_USER_ID), context.data.get(CTX_TG_USERNAME))):
        return {}
    if config.get("group_mode") == "off" and context.data.get(CTX_TG_CHAT_TYPE) != "private":
        return {}
    return config


def require_scope(context, project: str, profile: str) -> None:
    if not context_config(context, project=project, profile=profile):
        raise PermissionError("This Telegram bot or user is not allowed in that project/profile.")
    # Project activation can replace unavailable profiles; never authorize one and run another.
    from helpers import subagents
    if profile not in subagents.get_available_agents_dict(project or None):
        raise PermissionError("Choose an agent profile available in the destination project first.")


def can_select_session(source, target) -> bool:
    config = context_config(source, project=projects.get_context_project_name(target) or "", profile=target.config.profile)
    if not config:
        return False
    if target.data.get(CTX_TG_BOT):
        return all(source.data.get(key) == target.data.get(key)
                   for key in (CTX_TG_BOT, CTX_TG_USER_ID, CTX_TG_CHAT_ID))
    from plugins._telegram_integration.helpers.handler import _is_admin
    return _is_admin(config, source.data.get(CTX_TG_USER_ID), source.data.get(CTX_TG_USERNAME))


def remember_config(context, config: dict) -> None:
    context.data[CTX_TG_BOT_CFG] = {key: value for key, value in config.items()
                                  if key not in {"token", "webhook_secret"}}


def authorized_bot(context):
    from plugins._telegram_integration.helpers.bot_manager import get_bot
    try:
        config = context_config(context)
    except Exception:
        return None
    instance = get_bot(context.data.get(CTX_TG_BOT))
    if config and instance and instance.bot.token == config["token"]:
        return instance
    return None
