from helpers.api import ApiHandler, Input, Output, Request
from helpers.file_browser import FileBrowser
from helpers import extension
from api import get_work_dir_files
import posixpath


class RenameWorkDirFile(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        try:
            action = input.get("action", "rename")
            current_path = input.get("currentPath", "")

            if action == "move":
                file_paths = input.get("paths", [])
                destination_path = input.get("destinationPath", "")
                if not isinstance(file_paths, list) or not all(
                    isinstance(path, str) and path for path in file_paths
                ):
                    return {"error": "Paths are required"}
                if not isinstance(destination_path, str) or not destination_path:
                    return {"error": "Destination path is required"}
                file_paths = [
                    path if path.startswith("/") else f"/{path}"
                    for path in file_paths
                ]
                if not destination_path.startswith("/"):
                    destination_path = f"/{destination_path}"
                moved_paths = await move_items(file_paths, destination_path)
                res = bool(moved_paths)
                changed_paths = [*file_paths, *moved_paths]
            elif action in {"rename", "create-folder"}:
                new_name = (input.get("newName", "") or "").strip()
                if not new_name:
                    return {"error": "New name is required"}

                if action == "create-folder":
                    parent_path = input.get("parentPath", current_path)
                    if not parent_path:
                        return {"error": "Parent path is required"}
                    res = await create_folder(parent_path, new_name)
                    changed_paths = [
                        posixpath.join(str(parent_path).rstrip("/"), new_name)
                    ]
                else:
                    file_path = input.get("path", "")
                    if not file_path:
                        return {"error": "Path is required"}
                    if not file_path.startswith("/"):
                        file_path = f"/{file_path}"
                    res = await rename_item(file_path, new_name)
                    changed_paths = [
                        file_path,
                        posixpath.join(posixpath.dirname(file_path), new_name),
                    ]
            else:
                return {"error": "Unsupported file operation"}

            if res:
                await extension.call_extensions_async(
                    "workdir_file_mutation_after",
                    agent=None,
                    data={
                        "action": action,
                        "path": changed_paths[-1],
                        "paths": changed_paths,
                        "current_path": current_path,
                    },
                )
                result = await get_work_dir_files.get_files(current_path)
                return {"data": result}

            error_msg = {
                "create-folder": "Failed to create folder",
                "move": "Move failed",
            }.get(action, "Rename failed")
            return {"error": error_msg}

        except Exception as e:
            return {"error": str(e)}


async def rename_item(file_path: str, new_name: str) -> bool:
    browser = FileBrowser()
    return browser.rename_item(file_path, new_name)


async def create_folder(parent_path: str, folder_name: str) -> bool:
    browser = FileBrowser()
    return browser.create_folder(parent_path, folder_name)


async def move_items(file_paths: list[str], destination_path: str) -> list[str]:
    browser = FileBrowser()
    return browser.move_items(file_paths, destination_path)
