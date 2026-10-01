"""Telegram controls backed by the existing plugin and Agent Editor owners."""
from hashlib import sha256

from helpers import plugins, projects, tool_policy
from plugins._agent_editor.helpers import editor
from plugins._telegram_integration.helpers import telegram_client as tc


def _key(context, item):
    scope = f"{context.id}:{projects.get_context_project_name(context)}:{context.config.profile}:{item}"
    return sha256(scope.encode()).hexdigest()[:24]


def _plugin_items():
    return [(name, plugins.get_plugin_meta(name)) for name in sorted(plugins.get_plugins_list())
            if plugins.get_plugin_meta(name)]


async def show(context, token, chat_id, message_id, kind, page=0):
    if kind == "permissions" and context.config.profile == "default":
        raise ValueError("The Default utility profile has no editable permissions. Use /profile first.")
    items = _plugin_items() if kind == "plugins" else tool_policy.get_tool_catalog(context.agent0)
    page = min(max(0, page), max(0, (len(items) - 1) // 8))
    rows = []
    if kind == "plugins":
        title = "Installed plugins (instance-wide)"
        for name, meta in items[page * 8:page * 8 + 8]:
            enabled = plugins.get_toggle_state(name) == "enabled"
            locked = meta.always_enabled or name in {"_telegram_integration", "_commands"}
            action = "noop" if locked else ("off" if enabled else "on")
            rows.append([{"text": f"{'On' if enabled else 'Off'} — {meta.title}"[:64],
                          "callback_data": f"a0:plugin:{action}:{_key(context, name)}"}])
        title += "\nTap to enable or disable. Required plugins and this Telegram connection stay enabled here."
    else:
        policy = tool_policy.get_policy(context.agent0)
        title = f"Tool permissions: {context.config.profile}\nScope: {projects.get_context_project_name(context) or 'Global'}"
        for item in items[page * 8:page * 8 + 8]:
            allowed = tool_policy.resolve_tool(context.agent0, item['name'], canonical_id=item['id'], _policy=policy).allowed
            rows.append([{"text": f"{'Allow' if allowed else 'Block'} — {item['label']}"[:64],
                          "callback_data": f"a0:tool:{_key(context, item['id'])}"}])
        for field, label in (("default", "Tools default"), ("mcp_default", "MCP default")):
            value = policy[field] if policy['mode'] == 'custom' else 'allow'
            action = 'block' if value == 'allow' else 'allow'
            rows.append([{"text": f"{label}: {value}",
                          "callback_data": f"a0:policy:{field}:{action}:{_key(context, field)}"}])
        rows.append([{"text": "Use inherited policy", "callback_data": f"a0:policy:mode:inherit:{_key(context, 'mode')}"}])
    nav = []
    if page:
        nav.append({"text": "Prev", "callback_data": f"a0:{kind}page:{page - 1}"})
    if (page + 1) * 8 < len(items):
        nav.append({"text": "Next", "callback_data": f"a0:{kind}page:{page + 1}"})
    if nav:
        rows.append(nav)
    title += f"\nPage {page + 1}/{max(1, (len(items) + 7) // 8)}"
    await tc.raw_send_text(token, chat_id, title, message_id, None, {"inline_keyboard": rows})


def _save_policy(context, policy):
    if context.config.profile == "default" or context.is_running():
        raise ValueError("Choose an editable profile and stop the active run before changing permissions.")
    plan = editor.build_change_plan({"profile_id": context.config.profile, "tool_policy": policy}, context)
    editor.apply_change_plan(plan)


async def handle_callback(context, token, chat_id, message_id, action, value):
    actions = {"pluginspage", "permissionspage", "plugin", "tool", "toolset", "policy"}
    if action not in actions:
        return False
    if "_commands" not in plugins.get_enabled_plugins(context.agent0):
        raise ValueError("Commands is disabled for this chat.")
    if action in {"pluginspage", "permissionspage"}:
        await show(context, token, chat_id, message_id, action.removesuffix('page'), int(value))
    elif action == "plugin":
        desired, key = value.split(":", 1)
        if desired == 'noop':
            return True
        name, meta = next(((name, meta) for name, meta in _plugin_items() if _key(context, name) == key), (None, None))
        if not meta or meta.always_enabled or name in {"_telegram_integration", "_commands"} or desired not in {'on','off'}:
            raise ValueError("This plugin choice is unavailable. Send /plugins again.")
        plugins.toggle_plugin(name, desired == 'on')
        await show(context, token, chat_id, message_id, "plugins")
    elif action == "tool":
        item = next((item for item in tool_policy.get_tool_catalog(context.agent0) if _key(context, item['id']) == value), None)
        if not item:
            raise ValueError("This tool choice is no longer current. Send /permissions again.")
        await tc.raw_send_text(token, chat_id, item['label'] + "\n" + item.get('description', ''), message_id, None,
            {"inline_keyboard": [[{"text": label, "callback_data": f"a0:toolset:{choice}:{value}"}
                                   for choice, label in (("allow", "Allow"), ("block", "Block"), ("default", "Default"))]]})
    elif action == "toolset":
        desired, key = value.split(':', 1)
        item = next((item for item in tool_policy.get_tool_catalog(context.agent0) if _key(context, item['id']) == key), None)
        if not item or desired not in {'allow', 'block', 'default'}:
            raise ValueError("This tool choice is no longer current. Send /permissions again.")
        policy = tool_policy.get_policy(context.agent0)
        policy['mode'] = 'custom'
        for field in ('allowed', 'blocked'):
            policy[field] = [value for value in policy[field] if value != item['id']]
        if desired != 'default':
            policy['allowed' if desired == 'allow' else 'blocked'].append(item['id'])
        _save_policy(context, policy)
        await show(context, token, chat_id, message_id, 'permissions')
    elif action == "policy":
        field, desired, key = value.split(':', 2)
        if key != _key(context, field) or (field, desired) not in {
            ('mode', 'inherit'), ('default', 'allow'), ('default', 'block'), ('mcp_default', 'allow'), ('mcp_default', 'block')
        }:
            raise ValueError("This permission choice is no longer current. Send /permissions again.")
        policy = tool_policy.get_policy(context.agent0)
        policy.update(mode='custom')
        policy[field] = desired
        _save_policy(context, policy)
        await show(context, token, chat_id, message_id, 'permissions')
    return True
