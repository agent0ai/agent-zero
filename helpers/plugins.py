from __future__ import annotations

import asyncio
import re, json, glob
import time
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    TYPE_CHECKING,
    TypedDict,
)

from regex import W

from helpers import (
    files,
    git,
    notification,
    print_style,
    yaml as yaml_helper,
    cache,
    extension,
    watchdog,
    modules,
    functions,
)
from pydantic import BaseModel, Field

from helpers.defer import DeferredTask
from helpers.watchdog import WatchItem

if TYPE_CHECKING:
    from agent import Agent

# Extracts target selector from <meta name="plugin-target" content="...">
_META_TARGET_RE = re.compile(
    r'<meta\s+name=["\']plugin-target["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


type ToggleState = Literal["enabled", "disabled", "advanced"]


class PluginAssetFile(TypedDict):
    path: str
    project_name: str
    agent_profile: str


META_FILE_NAME = "plugin.yaml"
CONFIG_FILE_NAME = "config.json"
CONFIG_DEFAULT_FILE_NAME = "default_config.yaml"
DISABLED_FILE_NAME = ".toggle-0"
ENABLED_FILE_NAME = ".toggle-1"
TOGGLE_FILE_PATTERN = ".toggle-[01]"

HOOKS_SCRIPT = "hooks.py"
HOOKS_CACHE_AREA = "plugin_hooks(plugins)"
PLUGINS_LIST_CACHE_AREA = "plugins_list(plugins)"
ENABLED_PLUGINS_LIST_CACHE_AREA = "enabled_plugins(plugins)"
ENABLED_PLUGINS_PATHS_CACHE_AREA = "enabled_plugins_paths(plugins)"


_last_frontend_reload_notification_at = 0.0


class PluginMetadata(BaseModel):
    name: str = ""
    title: str = ""
    description: str = ""
    version: str = ""
    settings_sections: List[str] = Field(default_factory=list)
    per_project_config: bool = False
    per_agent_config: bool = False
    always_enabled: bool = False


class PluginListItem(BaseModel):
    name: str
    path: str
    display_name: str = ""
    description: str = ""
    version: str = ""
    author: str = ""
    repo: str = ""
    settings_sections: List[str] = Field(default_factory=list)
    per_project_config: bool = False
    per_agent_config: bool = False
    always_enabled: bool = False
    is_custom: bool = False
    has_main_screen: bool = False
    has_config_screen: bool = False
    has_readme: bool = False
    has_license: bool = False
    has_execute_script: bool = False
    toggle_state: ToggleState = "disabled"
    current_commit: str = ""
    current_commit_timestamp: str = ""
    thumbnail_url: str = ""


class PluginUpdateInfo(BaseModel):
    name: str
    path: str
    display_name: str = ""
    commits_since_local: int = 0
    last_remote_commit_at: str = ""
    branch: str = ""
    remote_branch: str = ""
    is_git_repo: bool = False
    is_remote: bool = False
    error: str = ""


def register_watchdogs():

    def on_plugin_change(events: list[WatchItem]):
        plugin_names: list[str] = []
        for path, _event in events:
            path = path.replace("\\", "/")
            if "/plugins/" not in path:
                continue
            plugin_name = path.split("/plugins/", 1)[1].split("/", 1)[0]
            if plugin_name and plugin_name not in plugin_names:
                plugin_names.append(plugin_name)
        print_style.PrintStyle.debug("Plugins watchdog triggered", plugin_names)
        python_change = any(path.endswith('.py') for path, _event in events)
        after_plugin_change(plugin_names or None, python_change=python_change)

    relevant_patterns = ["**/extensions/**/*", TOGGLE_FILE_PATTERN, HOOKS_SCRIPT]

    # combine relevant patterns with base path
    def expand_patterns(base_path: str):
        result = []
        for pattern in relevant_patterns:
            result.append(base_path + pattern)
        return result

    # add watchdogs for plugin roots
    watchdog.add_watchdog(
        id="plugins_roots",
        roots=get_plugin_roots(),
        patterns=[*expand_patterns("*/")],
        handler=on_plugin_change,
    )

    from helpers import projects
    from helpers import subagents

    # add watchdogs for plugin overrides in projects/plugins and projects/agents/plugins
    watchdog.add_watchdog(
        id="plugins_projects",
        roots=[files.get_abs_path(projects.PROJECTS_PARENT_DIR)],
        patterns=[
            *expand_patterns(f"*/{projects.PROJECT_META_DIR}/plugins/"),
            *expand_patterns(f"*/{projects.PROJECT_META_DIR}/agents/*/plugins/"),
        ],
        handler=on_plugin_change,
    )

    # add watchdogs for plugin overrides in /agents/plugins and /usr/agents/plugins
    watchdog.add_watchdog(
        id="plugins_agents",
        roots=[
            files.get_abs_path(subagents.DEFAULT_AGENTS_DIR),
            files.get_abs_path(subagents.USER_AGENTS_DIR),
        ],
        patterns=[*expand_patterns(f"*/plugins/*/")],
        handler=on_plugin_change,
    )


@extension.extensible
def after_plugin_change(plugin_names: list[str] | None = None, python_change:bool=False):
    clear_plugin_cache(plugin_names)
    if python_change:
        refresh_plugin_modules(plugin_names)
    send_frontend_reload_notification(plugin_names)


def refresh_plugin_modules(plugin_names: list[str] | None = None):
    if plugin_names:
        clear_plugins = any(name.startswith("_") for name in plugin_names)
        clear_usr_plugins = any(not name.startswith("_") for name in plugin_names)
        if clear_plugins:
            modules.purge_namespace("plugins")
        if clear_usr_plugins:
            modules.purge_namespace("usr.plugins")
    else:
        modules.purge_namespace("plugins")
        modules.purge_namespace("usr.plugins")


def clear_plugin_cache(plugin_names: list[str] | None = None):
    areas = ["*(plugins)*", "*(extensions)*", "*(api)*"]
    for area in areas:
        cache.clear(area)

    from helpers.websocket_manager import send_data

    DeferredTask().start_task(
        send_data,
        endpoint_name="/webui",
        event_name="clear_cache",
        data={"areas": areas},
    )


def get_plugin_roots(plugin_name: str = "") -> List[str]:
    """Plugin root directories, ordered by priority (user first)."""
    return [
        files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR, plugin_name),
        files.get_abs_path(files.PLUGINS_DIR, plugin_name),
    ]


def get_plugins_list():
    if cached := cache.get(PLUGINS_LIST_CACHE_AREA, ""):
        return cached

    result: list[str] = []
    seen_names: set[str] = set()
    for root in get_plugin_roots():
        for dir in Path(root).iterdir():
            if not dir.is_dir() or dir.name.startswith("."):
                continue
            if dir.name in seen_names:
                continue
            if files.exists(str(dir), META_FILE_NAME):
                seen_names.add(dir.name)
                result.append(dir.name)
    result.sort(key=lambda p: Path(p).name)

    cache.add(PLUGINS_LIST_CACHE_AREA, "", result)
    return result


def get_enhanced_plugins_list(
    custom: bool = True, builtin: bool = True, plugin_names: list[str] | None = None
) -> List[PluginListItem]:
    """Discover plugins by directory convention. First root wins on ID conflict."""
    results = []
    allowed_names = set(plugin_names) if plugin_names else None

    def load_plugins(root_path: str, is_custom: bool):
        for d in sorted(Path(root_path).iterdir(), key=lambda p: p.name):
            try:
                if not d.is_dir() or d.name.startswith("."):
                    continue
                if allowed_names is not None and d.name not in allowed_names:
                    continue
                meta_file = str(d / META_FILE_NAME)
                if not files.exists(meta_file):
                    continue
                meta = PluginMetadata.model_validate(files.read_file_yaml(meta_file))
                has_main_screen = files.exists(str(d / "webui" / "main.html"))
                has_config_screen = files.exists(str(d / "webui" / "config.html"))
                has_readme = files.exists(str(d / "README.md"))
                has_license = files.exists(str(d / "LICENSE"))
                has_execute_script = files.exists(str(d / "execute.py"))
                toggle_state = get_toggle_state(d.name)
                thumbnail_url = ""
                _thumb_exts = ("png", "jpg", "jpeg", "gif", "webp")
                for _ext in _thumb_exts:
                    _thumb = d / "webui" / f"thumbnail.{_ext}"
                    if _thumb.is_file():
                        thumbnail_url = f"/plugins/{d.name}/webui/thumbnail.{_ext}"
                        break
                current_commit = ""
                current_commit_timestamp = ""
                author = ""
                repo_name = ""
                if is_custom:
                    repo_info = git.get_repo_release_info(str(d))
                    if repo_info.is_git_repo:
                        author = repo_info.author
                        repo_name = repo_info.repo
                        if repo_info.head:
                            current_commit = repo_info.head.hash
                            current_commit_timestamp = repo_info.head.committed_at
                results.append(
                    PluginListItem(
                        name=d.name,
                        path=files.normalize_a0_path(str(d)),
                        display_name=meta.title or d.name,
                        description=meta.description,
                        version=meta.version,
                        author=author,
                        repo=repo_name,
                        settings_sections=meta.settings_sections,
                        per_project_config=meta.per_project_config,
                        per_agent_config=meta.per_agent_config,
                        always_enabled=meta.always_enabled,
                        is_custom=is_custom,
                        has_main_screen=has_main_screen,
                        has_config_screen=has_config_screen,
                        has_readme=has_readme,
                        has_license=has_license,
                        has_execute_script=has_execute_script,
                        toggle_state=toggle_state,
                        current_commit=current_commit,
                        current_commit_timestamp=current_commit_timestamp,
                        thumbnail_url=thumbnail_url,
                    )
                )
            except Exception as e:
                print_style.PrintStyle.error(f"Failed to load plugin {d.name}: {e}")
                continue

    if custom:
        load_plugins(files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR), True)
    if builtin:
        load_plugins(files.get_abs_path(files.PLUGINS_DIR), False)
    return results


def get_custom_plugins_updates(
    plugin_names: list[str] | None = None,
) -> List[PluginUpdateInfo]:
    plugins = get_enhanced_plugins_list(
        custom=True, builtin=False, plugin_names=plugin_names
    )
    results: list[PluginUpdateInfo] = []

    for plugin in plugins:
        update = git.get_remote_commits_since_local(plugin.path)
        results.append(
            PluginUpdateInfo(
                name=plugin.name,
                path=plugin.path,
                display_name=plugin.display_name,
                commits_since_local=update.commits_since_local,
                last_remote_commit_at=update.last_remote_commit_at,
                branch=update.branch,
                remote_branch=update.remote_branch,
                is_git_repo=update.is_git_repo,
                is_remote=update.is_remote,
                error=update.error,
            )
        )

    return results


def get_plugin_meta(plugin_name: str):
    plugin_dir = find_plugin_dir(plugin_name)
    if not plugin_dir:
        return None
    return PluginMetadata.model_validate(
        files.read_file_yaml(files.get_abs_path(plugin_dir, META_FILE_NAME))
    )


def find_plugin_dir(plugin_name: str):
    if not plugin_name:
        return None

    # check if the plugin is in the user directory
    user_plugin_path = files.get_abs_path(
        files.USER_DIR, files.PLUGINS_DIR, plugin_name, META_FILE_NAME
    )
    if files.exists(user_plugin_path):
        return files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR, plugin_name)

    # check if the plugin is in the default directory
    default_plugin_path = files.get_abs_path(
        files.PLUGINS_DIR, plugin_name, META_FILE_NAME
    )
    if files.exists(default_plugin_path):
        return files.get_abs_path(files.PLUGINS_DIR, plugin_name)

    return None


@extension.extensible
def uninstall_plugin(plugin_name):
    # call the uninstall hook if any
    call_plugin_hook(plugin_name, "uninstall")
    # then delete
    delete_plugin(plugin_name)


@extension.extensible
def delete_plugin(plugin_name: str):
    plugin_dir = find_plugin_dir(plugin_name)
    if not plugin_dir:
        raise FileNotFoundError(f"Plugin '{plugin_name}' not found")
    custom_plugins_dir = files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR)
    if not files.is_in_dir(plugin_dir, custom_plugins_dir):
        raise ValueError("Only custom plugins can be deleted")

    # delete additional plugin folders
    assets = [asset for asset in find_plugin_assets("", plugin_name=plugin_name) if not asset["path"].startswith(plugin_dir)]
    for asset in assets:
        files.delete_dir(asset["path"])

    send_frontend_reload_notification(
        [plugin_name]
    )  # send before deletion to properly check the extensions, second notification will be skipped automatically

    # does it have python files?
    python_change = bool(files.find_existing_paths_by_pattern(plugin_dir+"/**/*.py"))

    # delete main plugin folder
    files.delete_dir(plugin_dir)

    after_plugin_change([plugin_name], python_change=python_change)


def get_plugin_paths(*subpaths: str) -> List[str]:
    sub = "*/" + "/".join(subpaths) if subpaths else "*"
    paths: List[str] = []
    for root in get_plugin_roots():
        paths.extend(
            files.find_existing_paths_by_pattern(files.get_abs_path(root, sub))
        )
    return paths


def get_enabled_plugin_paths(agent: Agent | None, *subpaths: str) -> List[str]:
    if cached := cache.get(
        ENABLED_PLUGINS_PATHS_CACHE_AREA, cache.determine_cache_key(agent, *subpaths)
    ):
        return cached

    enabled = get_enabled_plugins(agent)
    paths: list[str] = []

    for plugin in enabled:
        base_dir = find_plugin_dir(plugin)
        if not base_dir:
            continue

        if not subpaths:
            if files.exists(base_dir):
                paths.append(base_dir)
            continue

        path_pattern = files.get_abs_path(base_dir, *subpaths)
        paths.extend(files.find_existing_paths_by_pattern(path_pattern))

    cache.add(
        ENABLED_PLUGINS_PATHS_CACHE_AREA,
        cache.determine_cache_key(agent, *subpaths),
        paths,
    )

    return paths


def get_enabled_plugins(agent: Agent | None):
    if cached := cache.get(
        ENABLED_PLUGINS_LIST_CACHE_AREA, cache.determine_cache_key(agent)
    ):
        return cached

    plugins = get_plugins_list()
    active = []

    for plugin in plugins:
        # plugins are toggled via .enabled / .disabled files
        # every plugin is on by default, unless disabled in usr dir
        enabled = True

        # root plugin paths
        plugin_paths = get_plugin_roots(plugin)

        # + agent paths
        if agent:
            from helpers import subagents

            agent_paths = subagents.get_paths(
                agent,
                files.PLUGINS_DIR,
                plugin,
                must_exist_completely=True,
                include_default=False,
                include_user=False,
                include_plugins=False,
                include_project=True,
            )
            plugin_paths = agent_paths + plugin_paths

        # go through paths in reverse order and determine the state
        enabled = determined_toggle_from_paths(enabled, reversed(plugin_paths))

        if enabled:
            active.append(plugin)

    cache.add(ENABLED_PLUGINS_LIST_CACHE_AREA, cache.determine_cache_key(agent), active)

    return active


def determined_toggle_from_paths(default: bool, paths: Iterator[str]):
    enabled = default
    for plugin_path in paths:
        if enabled:
            enabled = not files.exists(
                files.get_abs_path(plugin_path, DISABLED_FILE_NAME)
            )
        else:
            enabled = files.exists(files.get_abs_path(plugin_path, ENABLED_FILE_NAME))
    return enabled


def get_toggle_state(plugin_name: str) -> ToggleState:
    meta = get_plugin_meta(plugin_name)
    if not meta:
        return "disabled"
    if meta.always_enabled:
        return "enabled"

    # root plugin paths
    plugin_paths = get_plugin_roots(plugin_name)
    state = (
        "enabled"
        if determined_toggle_from_paths(True, reversed(plugin_paths))
        else "disabled"
    )

    # additional toggles in project/agent directories, return advanced
    if meta.per_agent_config or meta.per_project_config:
        configs = find_plugin_assets(
            TOGGLE_FILE_PATTERN,
            plugin_name=plugin_name,
            project_name="*" if meta.per_project_config else "",
            agent_profile="*" if meta.per_agent_config else "",
            only_first=False,
        )

        # Advanced if there are specific overrides (project or agent specific)
        if any(c.get("project_name") or c.get("agent_profile") for c in configs):
            state = "advanced"

    return state


@extension.extensible
def toggle_plugin(
    plugin_name: str,
    enabled: bool,
    project_name: str = "",
    agent_profile: str = "",
    clear_overrides: bool = False,
):
    if clear_overrides:
        all_toggles = find_plugin_assets(
            TOGGLE_FILE_PATTERN,
            plugin_name=plugin_name,
            project_name="*",
            agent_profile="*",
            only_first=False,
        )
        for toggle in all_toggles:
            files.delete_file(toggle["path"])

    enabled_file = determine_plugin_asset_path(
        plugin_name, project_name, agent_profile, ENABLED_FILE_NAME
    )
    disabled_file = determine_plugin_asset_path(
        plugin_name, project_name, agent_profile, DISABLED_FILE_NAME
    )

    # ensure clean state by deleting both potential files first
    files.delete_file(enabled_file)
    files.delete_file(disabled_file)

    if enabled:
        files.write_file(enabled_file, "")
    else:
        files.write_file(disabled_file, "")
    after_plugin_change([plugin_name])


@extension.extensible
def get_plugin_config(
    plugin_name: str,
    agent: Agent | None = None,
    project_name: str | None = None,
    agent_profile: str | None = None,
):

    default_used = False

    if project_name is None and agent is not None:
        from helpers import projects

        project_name = projects.get_context_project_name(agent.context)
    if agent_profile is None and agent is not None:
        agent_profile = agent.config.profile

    # find config.json in all possible places
    file = find_plugin_asset(
        plugin_name,
        CONFIG_FILE_NAME,
        project_name=project_name or "",
        agent_profile=agent_profile or "",
    )
    file_path = file.get("path", "") if file else ""

    # use default config if not found
    if not file_path:
        file_path = files.get_abs_path(
            find_plugin_dir(plugin_name), CONFIG_DEFAULT_FILE_NAME
        )
        default_used = True

    result = None
    if file_path and files.exists(file_path):
        result = (
            json.loads if file_path.lower().endswith(".json") else yaml_helper.loads
        )(files.read_file(file_path))

        if default_used:
            _apply_defaults_from_env(plugin_name, result)

    # call plugin hook to modify the standard result if needed
    result = call_plugin_hook(
        plugin_name,
        "get_plugin_config",
        default=result,
        agent=agent,
        project_name=project_name,
        agent_profile=agent_profile,
    )

    return result


def get_default_plugin_config(plugin_name: str):
    file_path = files.get_abs_path(
        find_plugin_dir(plugin_name), CONFIG_DEFAULT_FILE_NAME
    )

    # call plugin hook to get the result
    result = call_plugin_hook(
        plugin_name, "get_default_plugin_config", file_path=file_path
    )

    # or do standard load
    if result is None and file_path and files.exists(file_path):
        result = (
            json.loads if file_path.lower().endswith(".json") else yaml_helper.loads
        )(files.read_file(file_path))

    return result


@extension.extensible
def save_plugin_config(
    plugin_name: str, project_name: str, agent_profile: str, settings: dict
):
    file_path = determine_plugin_asset_path(
        plugin_name, project_name, agent_profile, CONFIG_FILE_NAME
    )

    # call plugin hook to get the result first
    new_settings = call_plugin_hook(
        plugin_name,
        "save_plugin_config",
        default=settings,
        project_name=project_name,
        agent_profile=agent_profile,
        settings=settings,
    )

    # or do standard load
    if new_settings is not None and file_path:
        files.write_file(file_path, json.dumps(new_settings))
        # after_plugin_change([plugin_name]) # don't trigger when only config changes


def find_plugin_asset(
    plugin_name: str, *subpaths: str, project_name="", agent_profile=""
):
    result = find_plugin_assets(
        *subpaths,
        plugin_name=plugin_name,
        project_name=project_name,
        agent_profile=agent_profile,
        only_first=True,
    )
    return result[0] if result else None


def find_plugin_assets(
    *subpaths: str,
    plugin_name: str = "*",
    project_name: str = "*",
    agent_profile: str = "*",
    only_first: bool = False,
) -> list[PluginAssetFile]:
    from helpers import projects, subagents

    results: list[PluginAssetFile] = []

    def _collect(path: str, proj: str, profile: str) -> bool:
        is_glob = glob.has_magic(path)
        matched_paths = (
            files.find_existing_paths_by_pattern(path)
            if is_glob
            else ([path] if files.exists(path) else [])
        )

        need_proj = proj == "*"
        need_prof = profile == "*"

        def _after(s: str, marker: str, last: bool = False) -> str:
            i = s.rfind(marker) if last else s.find(marker)
            if i == -1:
                return ""
            start = i + len(marker)
            end = s.find("/", start)
            return s[start:] if end == -1 else s[start:end]

        for matched in matched_paths:
            inferred_proj = _after(matched, "/projects/") if need_proj else proj
            inferred_prof = (
                _after(matched, "/agents/", last=True) if need_prof else profile
            )
            results.append(
                {
                    "project_name": inferred_proj,
                    "agent_profile": inferred_prof,
                    "path": matched,
                }
            )
            if only_first:
                return True
        return False

    # project/.a0proj/agents/<profile>/plugins/<plugin_name>/...
    if project_name:
        if agent_profile:
            path = projects.get_project_meta(
                project_name,
                files.AGENTS_DIR,
                agent_profile,
                files.PLUGINS_DIR,
                plugin_name,
                *subpaths,
            )
            if _collect(path, project_name, agent_profile):
                return results
        if not agent_profile or agent_profile == "*":
            # project/.a0proj/plugins/<plugin_name>/...
            path = projects.get_project_meta(
                project_name, files.PLUGINS_DIR, plugin_name, *subpaths
            )
            if _collect(path, project_name, ""):
                return results

    # usr/agents/<profile>/plugins/<plugin_name>/...
    if agent_profile:
        path = files.get_abs_path(
            subagents.USER_AGENTS_DIR,
            agent_profile,
            files.PLUGINS_DIR,
            plugin_name,
            *subpaths,
        )
        if _collect(path, "", agent_profile):
            return results

        # usr?/plugins/<any_plugin>/agents/<profile>/plugins/<plugin_name>/...
        for plugin_base in get_enabled_plugin_paths(None):
            path = files.get_abs_path(
                plugin_base,
                files.AGENTS_DIR,
                agent_profile,
                files.PLUGINS_DIR,
                plugin_name,
                *subpaths,
            )
            if _collect(path, "", agent_profile):
                return results

        # agents/<profile>/plugins/<plugin_name>/...
        path = files.get_abs_path(
            subagents.DEFAULT_AGENTS_DIR,
            agent_profile,
            files.PLUGINS_DIR,
            plugin_name,
            *subpaths,
        )
        if _collect(path, "", agent_profile):
            return results

    # usr/plugins/<plugin_name>/...
    path = files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR, plugin_name, *subpaths)
    if _collect(path, "", ""):
        return results

    # plugins/<plugin_name>/...
    path = files.get_abs_path(files.PLUGINS_DIR, plugin_name, *subpaths)
    _collect(path, "", "")

    return results


def determine_plugin_asset_path(
    plugin_name: str, project_name: str, agent_profile: str, *subpaths: str
):
    base_path = files.get_abs_path(files.USER_DIR)

    if project_name:
        from helpers import projects

        base_path = projects.get_project_meta(project_name)

    if agent_profile:
        base_path = files.get_abs_path(base_path, files.AGENTS_DIR, agent_profile)

    return files.get_abs_path(base_path, files.PLUGINS_DIR, plugin_name, *subpaths)


def send_frontend_reload_notification(plugin_names: list[str] | None = None):
    """If the plugin changed has webui extensions, notify frontend to reload the page"""
    global _last_frontend_reload_notification_at

    display_time = 5
    now = time.monotonic()
    if now - _last_frontend_reload_notification_at < display_time:
        return

    if plugin_names:
        has_webui_extension = False
        for plugin_name in plugin_names:
            plugin_dir = find_plugin_dir(plugin_name)
            if plugin_dir and files.exists(
                files.get_abs_path(plugin_dir, "extensions", "webui")
            ):
                has_webui_extension = True
                break
        if not has_webui_extension:
            return

    async def _send_later():
        global _last_frontend_reload_notification_at

        await asyncio.sleep(1)

        _last_frontend_reload_notification_at = time.monotonic()

        notification.NotificationManager.send_notification(
            type=notification.NotificationType.INFO,
            priority=notification.NotificationPriority.NORMAL,
            title="Plugins with frontend extensions updated, page reload recommended",
            message="""<button type="button" class="button confirm" onclick="window.location.reload()"><span class="icon material-symbols-outlined">refresh</span>Reload page</button>""",
            detail="",
            display_time=display_time,
            group="plugins_changed",
            id="plugins_frontend_reload",
        )

    DeferredTask().start_task(_send_later)


def call_plugin_hook(
    plugin_name: str, hook_name: str, default: Any = None, *args, **kwargs
):
    hooks = None

    # use cached hooks if enabled
    if not cache.has(HOOKS_CACHE_AREA, plugin_name):
        plugin_dir = find_plugin_dir(plugin_name)
        if not plugin_dir:
            return default  # plugin directory not found, skip hooks
        hooks_script = files.get_abs_path(plugin_dir, HOOKS_SCRIPT)
        hooks = (
            modules.import_module(hooks_script) if files.exists(hooks_script) else None
        )
        cache.add(HOOKS_CACHE_AREA, plugin_name, hooks)
    else:
        hooks = cache.get(HOOKS_CACHE_AREA, plugin_name)

    if not hooks:
        return default

    hook = getattr(hooks, hook_name, None)
    if not hook:
        return default

    if asyncio.iscoroutinefunction(hook):
        return asyncio.run(functions.safe_call(hook, *args, default=default, **kwargs))

    return functions.safe_call(hook, *args, default=default, **kwargs)


def _apply_defaults_from_env(plugin_name: str, config: dict[str, Any]):
    from helpers.settings import get_default_value

    def _apply(prefix: list[str], value: dict[str, Any]):
        for key, child in value.items():
            env_name = "__".join([plugin_name, *prefix, key])
            value[key] = get_default_value(env_name, child)
            if isinstance(value[key], dict):
                _apply([*prefix, key], value[key])

    _apply([], config)
