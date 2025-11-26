from python.helpers import files
from typing import TypedDict, TYPE_CHECKING
from pydantic import BaseModel, model_validator
import json
from typing import Literal

GLOBAL_DIR = "."
USER_DIR = "usr"
DEFAULT_AGENTS_DIR = "agents"
USER_AGENTS_DIR = "usr/agents"

type Origin = Literal["default", "user", "project"]

if TYPE_CHECKING:
    from agent import Agent


class SubAgentListItem(BaseModel):
    name: str = ""
    title: str = ""
    description: str = ""
    context: str = ""
    origin: list[Origin] = []
    enabled: bool = True

    @model_validator(mode="after")
    def post_validator(self):
        if self.title == "":
            self.title = self.name
        return self


class SubAgent(SubAgentListItem):
    prompts: dict[str, str] = {}


def get_agents_list(project_name: str | None = None) -> list[SubAgentListItem]:
    return list(get_agents_dict(project_name).values())


def get_agents_dict(
    project_name: str | None = None,
) -> dict[str, SubAgentListItem]:
    def _merge_agent_dicts(
        base: dict[str, SubAgentListItem],
        overrides: dict[str, SubAgentListItem],
    ) -> dict[str, SubAgentListItem]:
        merged: dict[str, SubAgentListItem] = dict(base)
        for name, override in overrides.items():
            base_agent = merged.get(name)
            merged[name] = (
                _merge_agent_list_items(base_agent, override)
                if base_agent
                else override
            )
        return merged

    # load default and custom agents and merge
    default_agents = _get_agents_list_from_dir(DEFAULT_AGENTS_DIR, origin="default")
    custom_agents = _get_agents_list_from_dir(USER_AGENTS_DIR, origin="user")
    merged = _merge_agent_dicts(default_agents, custom_agents)

    # merge with project agents if possible
    if project_name:
        from python.helpers import projects

        project_agents_dir = projects.get_project_meta_folder(project_name, "agents")
        project_agents = _get_agents_list_from_dir(project_agents_dir, origin="project")
        merged = _merge_agent_dicts(merged, project_agents)

    return merged


def _get_agents_list_from_dir(dir: str, origin: Origin) -> dict[str, SubAgentListItem]:
    result: dict[str, SubAgentListItem] = {}
    subdirs = files.get_subdirectories(dir)

    for subdir in subdirs:
        try:
            agent_json = files.read_file(files.get_abs_path(dir, subdir, "agent.json"))
            agent_data = SubAgentListItem.model_validate_json(agent_json)
            name = agent_data.name or subdir
            agent_data.name = name
            agent_data.origin = [origin]
            result[name] = agent_data
        except Exception:
            continue

    return result


def load_agent_data(name: str, project_name: str | None = None) -> SubAgent:
    def _merge_agent(
        original: SubAgent | None, override: SubAgent | None = None
    ) -> SubAgent | None:
        if original and override:
            return _merge_agents(original, override)
        elif original:
            return original
        return override

    # load default and user agents and merge
    default_agent = _load_agent_data_from_dir(
        DEFAULT_AGENTS_DIR, name, origin="default"
    )
    user_agent = _load_agent_data_from_dir(USER_AGENTS_DIR, name, origin="user")
    merged = _merge_agent(default_agent, user_agent)

    # merge with project agent if possible
    if project_name:
        from python.helpers import projects

        project_agents_dir = projects.get_project_meta_folder(project_name, "agents")
        project_agent = _load_agent_data_from_dir(
            project_agents_dir, name, origin="project"
        )
        merged = _merge_agent(merged, project_agent)

    if merged is None:
        raise FileNotFoundError(
            f"Agent '{name}' not found in default or custom directories"
        )

    return merged


def save_agent_data(name: str, subagent: SubAgent) -> None:
    # write agent.json in custom directory
    agent_dir = f"{USER_AGENTS_DIR}/{name}"
    agent_json = {
        "title": subagent.title,
        "description": subagent.description,
        "context": subagent.context,
        "enabled": subagent.enabled,
    }
    files.write_file(f"{agent_dir}/agent.json", json.dumps(agent_json, indent=2))

    # replace prompts in custom directory
    prompts_dir = f"{agent_dir}/prompts"
    # clear existing custom prompts directory (if any)
    files.delete_dir(prompts_dir)

    prompts = subagent.prompts or {}
    for name, content in prompts.items():
        safe_name = files.safe_file_name(name)
        if not safe_name.endswith(".md"):
            safe_name += ".md"
        files.write_file(f"{prompts_dir}/{safe_name}", content)


def delete_agent_data(name: str) -> None:
    files.delete_dir(f"{USER_AGENTS_DIR}/{name}")


def _load_agent_data_from_dir(dir: str, name: str, origin: Origin) -> SubAgent | None:
    try:
        subagent_json = files.read_file(files.get_abs_path(dir, name, "agent.json"))
        subagent = SubAgent.model_validate_json(subagent_json)
    except Exception:
        # backward compatibility (before agent.json existed)
        try:
            context_file = files.read_file(files.get_abs_path(dir, name, "_context.md"))
        except Exception:
            context_file = ""
        subagent = SubAgent(
            name=name,
            title=name,
            description="",
            context=context_file,
            origin=[origin],
            prompts={},
        )

    # non-stored fields
    subagent.name = name
    subagent.origin = [origin]

    prompts_dir = f"{dir}/{name}/prompts"
    try:
        prompts = files.read_text_files_in_dir(prompts_dir, pattern="*.md")
    except Exception:
        prompts = {}

    subagent.prompts = prompts or {}
    return subagent


def _merge_agents(base: SubAgent | None, override: SubAgent | None) -> SubAgent | None:
    if base is None:
        return override
    if override is None:
        return base

    merged_prompts: dict[str, str] = {}
    merged_prompts.update(base.prompts or {})
    merged_prompts.update(override.prompts or {})

    return SubAgent(
        name=override.name,
        title=override.title,
        description=override.description,
        context=override.context,
        origin=_merge_origins(base.origin, override.origin),
        prompts=merged_prompts,
    )


def _merge_agent_list_items(
    base: SubAgentListItem, override: SubAgentListItem
) -> SubAgentListItem:
    return SubAgentListItem(
        name=override.name or base.name,
        title=override.title or base.title,
        description=override.description or base.description,
        context=override.context or base.context,
        origin=_merge_origins(base.origin, override.origin),
    )


def _merge_origins(base: list[Origin], override: list[Origin]) -> list[Origin]:
    return base + override


def get_default_promp_file_names() -> list[str]:
    return files.list_files("prompts", filter="*.md")


def get_available_agents_dict(
    project_name: str | None,
) -> dict[str, SubAgentListItem]:
    # all available agents
    all_agents = get_agents_dict()
    # filter by project settings
    from python.helpers import projects

    project_settings = (
        projects.load_project_subagents(project_name) if project_name else {}
    )

    filtered_agents: dict[str, SubAgentListItem] = {}
    for name, agent in all_agents.items():
        if name in project_settings:
            agent.enabled = project_settings[name]["enabled"]
        if agent.enabled:
            filtered_agents[name] = agent
    return filtered_agents


def get_agent_paths(
    agent: "Agent", *subpaths, must_exist_completely: bool = True
) -> list[str]:
    """Returns list of possible paths for the given agent and subpaths. Order is from lowest priority (global)."""

    if not agent or not agent.config.profile:
        return []
    from python.helpers import projects

    project_name = projects.get_context_project_name(agent.context)
    return get_agent_profile_paths(
        agent.config.profile,
        project_name,
        *subpaths,
        must_exist_completely=must_exist_completely,
    )


def get_agent_paths_chain(
    agent: "Agent|None",
    *subpaths,
    must_exist_completely: bool = True,
    include_project: bool = True,
    include_user: bool = True,
    include_default: bool = True,
    default_root: str = "",
) -> list[str]:
    """Returns list of file paths for the given agent and subpaths, searched in order of priority:
    project/agents/, usr/agents/, agents/, project/, usr/, default."""
    from python.helpers import projects

    if agent and agent.config.profile:
        project_name = projects.get_context_project_name(agent.context)
        paths = get_agent_profile_paths(
            agent.config.profile,
            project_name,
            *subpaths,
            must_exist_completely=must_exist_completely,
        )
        list.reverse(paths)  # reverse for proper priority
    else:
        paths = []
        project_name = ""

    if include_project and project_name:
        path = projects.get_project_meta_folder(project_name, *subpaths)
        if (not must_exist_completely) or files.exists(path):
            paths.append(path)
    if include_user:
        path = files.get_abs_path(USER_DIR, *subpaths)
        if (not must_exist_completely) or files.exists(path):
            paths.append(path)
    if include_default:
        path = files.get_abs_path(default_root, *subpaths)
        if (not must_exist_completely) or files.exists(path):
            paths.append(path)
    return paths


def get_agent_profile_paths(
    name: str,
    project_name: str | None = None,
    *subpaths,
    must_exist_completely: bool = True,
) -> list[str]:
    result = []
    check_subpaths = subpaths if must_exist_completely else []

    if files.exists(files.get_abs_path(DEFAULT_AGENTS_DIR, name, *check_subpaths)):
        result.append(files.get_abs_path(DEFAULT_AGENTS_DIR, name, *subpaths))
    if files.exists(files.get_abs_path(USER_AGENTS_DIR, name, *check_subpaths)):
        result.append(files.get_abs_path(USER_AGENTS_DIR, name, *subpaths))
    if project_name:
        from python.helpers import projects

        project_agent_dir = projects.get_project_meta_folder(
            project_name, "agents", name
        )
        if files.exists(files.get_abs_path(project_agent_dir, *check_subpaths)):
            result.append(files.get_abs_path(project_agent_dir, *subpaths))
    return result
