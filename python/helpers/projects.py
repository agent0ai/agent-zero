import os
from typing import Literal, TypedDict, TYPE_CHECKING

from python.helpers import files, dirty_json, persist_chat, file_tree
from python.helpers.print_style import PrintStyle


if TYPE_CHECKING:
    from agent import AgentContext

PROJECTS_PARENT_DIR = "usr/projects"
PROJECT_META_DIR = ".a0proj"
PROJECT_INSTRUCTIONS_DIR = "instructions"
PROJECT_KNOWLEDGE_DIR = "knowledge"
PROJECT_HEADER_FILE = "project.json"

CONTEXT_DATA_KEY_PROJECT = "project"


class FileStructureInjectionSettings(TypedDict):
    enabled: bool
    max_depth: int
    max_files: int
    max_folders: int
    max_lines: int
    gitignore: str

class SubAgentSettings(TypedDict):
    enabled: bool
    
class BasicProjectData(TypedDict):
    title: str
    description: str
    instructions: str
    color: str
    memory: Literal[
        "own", "global"
    ]  # in the future we can add cutom and point to another existing folder
    file_structure: FileStructureInjectionSettings

class EditProjectData(BasicProjectData):
    name: str
    instruction_files_count: int
    knowledge_files_count: int
    variables: str
    secrets: str
    subagents: dict[str, SubAgentSettings]



def get_projects_parent_folder():
    return files.get_abs_path(PROJECTS_PARENT_DIR)


def get_project_folder(name: str):
    return files.get_abs_path(get_projects_parent_folder(), name)


def get_project_meta_folder(name: str, *sub_dirs: str):
    return files.get_abs_path(get_project_folder(name), PROJECT_META_DIR, *sub_dirs)


def delete_project(name: str):
    abs_path = files.get_abs_path(PROJECTS_PARENT_DIR, name)
    files.delete_dir(abs_path)
    deactivate_project_in_chats(name)
    return name


def create_project(name: str, data: BasicProjectData):
    abs_path = files.create_dir_safe(
        files.get_abs_path(PROJECTS_PARENT_DIR, name), rename_format="{name}_{number}"
    )
    create_project_meta_folders(name)
    data = _normalizeBasicData(data)
    save_project_header(name, data)
    return name


def load_project_header(name: str):
    abs_path = files.get_abs_path(
        PROJECTS_PARENT_DIR, name, PROJECT_META_DIR, PROJECT_HEADER_FILE
    )
    header: dict = dirty_json.parse(files.read_file(abs_path))  # type: ignore
    header["name"] = name
    return header


def _default_file_structure_settings():
    try:
        gitignore = files.read_file("conf/projects.default.gitignore")
    except Exception:
        gitignore = ""
    return FileStructureInjectionSettings(
        enabled=True,
        max_depth=5,
        max_files=20,
        max_folders=20,
        max_lines=250,
        gitignore=gitignore,
    )


def _normalizeBasicData(data: BasicProjectData):
    return BasicProjectData(
        title=data.get("title", ""),
        description=data.get("description", ""),
        instructions=data.get("instructions", ""),
        color=data.get("color", ""),
        memory=data.get("memory", "own"),
        file_structure=data.get(
            "file_structure",
            _default_file_structure_settings(),
        ),
    )


def _normalizeEditData(data: EditProjectData):
    return EditProjectData(
        name=data.get("name", ""),
        title=data.get("title", ""),
        description=data.get("description", ""),
        instructions=data.get("instructions", ""),
        variables=data.get("variables", ""),
        color=data.get("color", ""),
        instruction_files_count=data.get("instruction_files_count", 0),
        knowledge_files_count=data.get("knowledge_files_count", 0),
        secrets=data.get("secrets", ""),
        memory=data.get("memory", "own"),
        file_structure=data.get(
            "file_structure",
            _default_file_structure_settings(),
        ),
        subagents=data.get("subagents", {}),
    )


def _edit_data_to_basic_data(data: EditProjectData):
    return _normalizeBasicData(data)


def _basic_data_to_edit_data(data: BasicProjectData):
    return _normalizeEditData(data)  # type: ignore


def update_project(name: str, data: EditProjectData):
    # merge with current state
    current = load_edit_project_data(name)
    current.update(data)
    current = _normalizeEditData(current)

    # save header data
    header = _edit_data_to_basic_data(current)
    save_project_header(name, header)

    # save secrets
    save_project_variables(name, current["variables"])
    save_project_secrets(name, current["secrets"])
    save_project_subagents(name, current["subagents"])

    reactivate_project_in_chats(name)
    return name


def load_basic_project_data(name: str) -> BasicProjectData:
    data = BasicProjectData(**load_project_header(name))
    normalized = _normalizeBasicData(data)
    return normalized


def load_edit_project_data(name: str) -> EditProjectData:
    data = load_basic_project_data(name)
    additional_instructions = get_additional_instructions_files(
        name
    )  # for additional info
    variables = load_project_variables(name)
    secrets = load_project_secrets_masked(name)
    subagents = load_project_subagents(name)
    knowledge_files_count = get_knowledge_files_count(name)
    data = EditProjectData(
        **data,
        name=name,
        instruction_files_count=len(additional_instructions),
        knowledge_files_count=knowledge_files_count,
        variables=variables,
        secrets=secrets,
        subagents=subagents,
    )
    data = _normalizeEditData(data)
    return data


def save_project_header(name: str, data: BasicProjectData):
    # save project header file
    header = dirty_json.stringify(data)
    abs_path = files.get_abs_path(
        PROJECTS_PARENT_DIR, name, PROJECT_META_DIR, PROJECT_HEADER_FILE
    )

    files.write_file(abs_path, header)


def get_active_projects_list():
    return _get_projects_list(get_projects_parent_folder())


def _get_projects_list(parent_dir):
    projects = []

    # folders in project directory
    for name in os.listdir(parent_dir):
        try:
            abs_path = os.path.join(parent_dir, name)
            if os.path.isdir(abs_path):
                project_data = load_basic_project_data(name)
                projects.append(
                    {
                        "name": name,
                        "title": project_data.get("title", ""),
                        "description": project_data.get("description", ""),
                        "color": project_data.get("color", ""),
                    }
                )
        except Exception as e:
            PrintStyle.error(f"Error loading project {name}: {str(e)}")

    # sort projects by name
    projects.sort(key=lambda x: x["name"])
    return projects


def activate_project(context_id: str, name: str):
    from agent import AgentContext

    data = load_edit_project_data(name)
    context = AgentContext.get(context_id)
    if context is None:
        raise Exception("Context not found")
    display_name = str(data.get("title", name))
    display_name = display_name[:22] + "..." if len(display_name) > 25 else display_name
    context.set_data(CONTEXT_DATA_KEY_PROJECT, name)
    context.set_output_data(
        CONTEXT_DATA_KEY_PROJECT,
        {"name": name, "title": display_name, "color": data.get("color", "")},
    )

    # persist
    persist_chat.save_tmp_chat(context)


def deactivate_project(context_id: str):
    from agent import AgentContext

    context = AgentContext.get(context_id)
    if context is None:
        raise Exception("Context not found")
    context.set_data(CONTEXT_DATA_KEY_PROJECT, None)
    context.set_output_data(CONTEXT_DATA_KEY_PROJECT, None)

    # persist
    persist_chat.save_tmp_chat(context)


def reactivate_project_in_chats(name: str):
    from agent import AgentContext

    for context in AgentContext.all():
        if context.get_data(CONTEXT_DATA_KEY_PROJECT) == name:
            activate_project(context.id, name)
        persist_chat.save_tmp_chat(context)


def deactivate_project_in_chats(name: str):
    from agent import AgentContext

    for context in AgentContext.all():
        if context.get_data(CONTEXT_DATA_KEY_PROJECT) == name:
            deactivate_project(context.id)
        persist_chat.save_tmp_chat(context)


def build_system_prompt_vars(name: str):
    project_data = load_basic_project_data(name)
    main_instructions = project_data.get("instructions", "") or ""
    additional_instructions = get_additional_instructions_files(name)
    complete_instructions = (
        main_instructions
        + "\n\n".join(
            additional_instructions[k] for k in sorted(additional_instructions)
        )
    ).strip()
    return {
        "project_name": project_data.get("title", ""),
        "project_description": project_data.get("description", ""),
        "project_instructions": complete_instructions or "",
        "project_path": files.normalize_a0_path(get_project_folder(name)),
    }


def get_additional_instructions_files(name: str):
    instructions_folder = files.get_abs_path(
        get_project_folder(name), PROJECT_META_DIR, PROJECT_INSTRUCTIONS_DIR
    )
    return files.read_text_files_in_dir(instructions_folder)


def get_context_project_name(context: "AgentContext") -> str | None:
    return context.get_data(CONTEXT_DATA_KEY_PROJECT)


def load_project_variables(name: str):
    try:
        abs_path = files.get_abs_path(get_project_meta_folder(name), "variables.env")
        return files.read_file(abs_path)
    except Exception:
        return ""


def save_project_variables(name: str, variables: str):
    abs_path = files.get_abs_path(get_project_meta_folder(name), "variables.env")
    files.write_file(abs_path, variables)


def load_project_subagents(name: str) -> dict[str, SubAgentSettings]:
    try:
        abs_path = files.get_abs_path(get_project_meta_folder(name), "agents.json")
        data = dirty_json.parse(files.read_file(abs_path))
        if isinstance(data, dict):
            return _normalize_subagents(data)  # type: ignore[arg-type,return-value]
        return {}
    except Exception:
        return {}


def save_project_subagents(name: str, subagents_data: dict[str, SubAgentSettings]):
    abs_path = files.get_abs_path(get_project_meta_folder(name), "agents.json")
    normalized = _normalize_subagents(subagents_data)
    content = dirty_json.stringify(normalized)
    files.write_file(abs_path, content)


def _normalize_subagents(
    subagents_data: dict[str, SubAgentSettings]
) -> dict[str, SubAgentSettings]:
    from python.helpers import subagents

    agents_dict = subagents.get_agents_dict()

    normalized: dict[str, SubAgentSettings] = {}
    for key, value in subagents_data.items():
        agent = agents_dict.get(key)
        if not agent:
            continue

        enabled = bool(value["enabled"])
        if agent.enabled == enabled:
            continue

        normalized[key] = {"enabled": enabled}

    return normalized


def load_project_secrets_masked(name: str, merge_with_global=False):
    from python.helpers import secrets

    mgr = secrets.get_project_secrets_manager(name, merge_with_global)
    return mgr.get_masked_secrets()


def save_project_secrets(name: str, secrets: str):
    from python.helpers.secrets import get_project_secrets_manager

    secrets_manager = get_project_secrets_manager(name)
    secrets_manager.save_secrets_with_merge(secrets)


def get_context_memory_subdir(context: "AgentContext") -> str | None:
    # if a project is active and has memory isolation set, return the project memory subdir
    project_name = get_context_project_name(context)
    if project_name:
        project_data = load_basic_project_data(project_name)
        if project_data["memory"] == "own":
            return "projects/" + project_name
    return None  # no memory override


def create_project_meta_folders(name: str):
    # create instructions folder
    files.create_dir(get_project_meta_folder(name, PROJECT_INSTRUCTIONS_DIR))

    # create knowledge folders
    files.create_dir(get_project_meta_folder(name, PROJECT_KNOWLEDGE_DIR))
    from python.helpers import memory

    for memory_type in memory.Memory.Area:
        files.create_dir(
            get_project_meta_folder(name, PROJECT_KNOWLEDGE_DIR, memory_type.value)
        )


def get_knowledge_files_count(name: str):
    knowledge_folder = files.get_abs_path(
        get_project_meta_folder(name, PROJECT_KNOWLEDGE_DIR)
    )
    return len(files.list_files_in_dir_recursively(knowledge_folder))

def get_file_structure(name: str, basic_data: BasicProjectData|None=None) -> str:
    project_folder = get_project_folder(name)
    if basic_data is None:
        basic_data = load_basic_project_data(name)
    
    tree = str(file_tree.file_tree(
        project_folder,
        max_depth=basic_data["file_structure"]["max_depth"],
        max_files=basic_data["file_structure"]["max_files"],
        max_folders=basic_data["file_structure"]["max_folders"],
        max_lines=basic_data["file_structure"]["max_lines"],
        ignore=basic_data["file_structure"]["gitignore"],
        output_mode=file_tree.OUTPUT_MODE_STRING
    ))

    # empty?
    if "\n" not in tree:
        tree += "\n # Empty"

    return tree

    