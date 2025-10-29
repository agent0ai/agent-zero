import os
from typing import TypedDict

from python.helpers import files, dirty_json, persist_chat
from python.helpers.print_style import PrintStyle

PROJECTS_PARENT_DIR = "usr/projects"
PROJECTS_ARCHIVE_DIR = "usr/projects-archived"
PROJECT_META_DIR = ".a0proj"
PROJECT_INSTRUCTIONS_DIR = "instructions"
PROJECT_HEADER_FILE = "project.json"

CONTEXT_DATA_KEY_PROJECT_PATH = "project_path"
CONTEXT_DATA_KEY_PROJECT_COLOR = "project_color"
CONTEXT_DATA_KEY_PROJECT_NAME = "project_name"


class BasicProjectData(TypedDict):
    title: str | None
    description: str | None
    instructions: str | None
    color: str | None


class EditProjectData(BasicProjectData):
    name: str
    path: str


def get_projects_parent_folder():
    return files.get_abs_path(PROJECTS_PARENT_DIR)


def get_projects_archive_folder():
    return files.get_abs_path(PROJECTS_ARCHIVE_DIR)


def get_project_folder(name: str):
    return files.get_abs_path(get_projects_parent_folder(), name)


def get_archived_project_folder(name: str):
    return files.get_abs_path(get_projects_archive_folder(), name)


def archive_project(name: str):
    return files.move_dir_safe(
        get_project_folder(name), get_archived_project_folder(name), rename_format="{name}_{number}"
    )


def unarchive_project(name: str):
    return files.move_dir_safe(
        get_archived_project_folder(name), get_project_folder(name), rename_format="{name}_{number}"
    )


def delete_project(path: str):
    files.delete_dir(path)
    deactivate_project_in_chats(path)
    return path


def create_project(name: str, data: BasicProjectData):
    new_path = files.create_dir_safe(get_project_folder(name), rename_format="{name}_{number}")
    data = _normalizeBasicData(data)
    save_project_files(new_path, data)
    return new_path


def load_project_header(path: str):
    header: dict = dirty_json.parse(
        files.read_file(files.get_abs_path(path, PROJECT_META_DIR, PROJECT_HEADER_FILE))
    )  # type: ignore
    header["path"] = path
    return header


def _normalizeBasicData(data: BasicProjectData):
    return BasicProjectData(
        title=data.get("title", ""),
        description=data.get("description", ""),
        instructions=data.get("instructions", ""),
        color=data.get("color", ""),
    )


def update_project(path: str, data: BasicProjectData):
    current: BasicProjectData = load_edit_project_data(path)  # type: ignore
    current.update(_normalizeBasicData(data))
    save_project_files(path, current)
    reactivate_project_in_chats(path)
    return path


def load_edit_project_data(path: str) -> BasicProjectData:
    data = BasicProjectData(
        **dirty_json.parse(
            files.read_file(
                files.get_abs_path(path, PROJECT_META_DIR, PROJECT_HEADER_FILE)
            )
        )  # type: ignore
    )
    data = _normalizeBasicData(data)
    data = EditProjectData(**data, name=os.path.basename(path), path=path)
    return data  # type: ignore


def save_project_files(path: str, data: BasicProjectData):
    # save project header file
    header = dirty_json.stringify(data)
    files.write_file(
        files.get_abs_path(path, PROJECT_META_DIR, PROJECT_HEADER_FILE), header
    )


def get_active_projects_list():
    return _get_projects_list(get_projects_parent_folder())


def get_archived_projects_list():
    return _get_projects_list(get_projects_archive_folder())


def _get_projects_list(parent_dir):
    projects = []

    # folders in project directory
    for name in os.listdir(parent_dir):
        try:
            path = os.path.join(parent_dir, name)
            if os.path.isdir(path):

                project_data = load_edit_project_data(path)

                projects.append(
                    {
                        "name": name,
                        "path": path,
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


def activate_project(context_id: str, path: str):
    from agent import AgentContext

    data = load_edit_project_data(path)
    context = AgentContext.get(context_id)
    if context is None:
        raise Exception("Context not found")
    name = str(data.get("title", data.get("name", data.get("path", ""))))
    name = name[:22] + "..." if len(name) > 25 else name
    context.set_data(CONTEXT_DATA_KEY_PROJECT_PATH, path)
    context.set_output_data(CONTEXT_DATA_KEY_PROJECT_PATH, path)
    context.set_output_data(CONTEXT_DATA_KEY_PROJECT_COLOR, data.get("color", ""))
    context.set_output_data(CONTEXT_DATA_KEY_PROJECT_NAME, name)

    # persist
    persist_chat.save_tmp_chat(context)


def deactivate_project(context_id: str):
    from agent import AgentContext

    context = AgentContext.get(context_id)
    if context is None:
        raise Exception("Context not found")
    context.set_data(CONTEXT_DATA_KEY_PROJECT_PATH, None)
    context.set_output_data(CONTEXT_DATA_KEY_PROJECT_PATH, None)
    context.set_output_data(CONTEXT_DATA_KEY_PROJECT_COLOR, None)
    context.set_output_data(CONTEXT_DATA_KEY_PROJECT_NAME, None)

    # persist
    persist_chat.save_tmp_chat(context)


def reactivate_project_in_chats(path: str):
    from agent import AgentContext

    for context in AgentContext.all():
        if context.get_data(CONTEXT_DATA_KEY_PROJECT_PATH) == path:
            activate_project(context.id, path)
        persist_chat.save_tmp_chat(context)

def deactivate_project_in_chats(path: str):
    from agent import AgentContext

    for context in AgentContext.all():
        if context.get_data(CONTEXT_DATA_KEY_PROJECT_PATH) == path:
            deactivate_project(context.id)
        persist_chat.save_tmp_chat(context)

def build_system_prompt_vars(project_path: str):
    project_data = load_edit_project_data(project_path)
    return {
        "project_path": project_path,
        "project_name": project_data.get("title", ""),
        "project_description": project_data.get("description", ""),
        "project_instructions": project_data.get("instructions", ""),
    }

