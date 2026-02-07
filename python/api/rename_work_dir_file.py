from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers.file_browser import FileBrowser
from python.helpers import runtime
from python.api import get_work_dir_files


class RenameWorkDirFile(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        try:
            action = input.get("action", "rename")
            new_name = (input.get("newName", "") or "").strip()
            if not new_name:
                return {"error": "New name is required"}

            current_path = input.get("currentPath", "")

            if action == "create-folder":
                parent_path = input.get("parentPath", current_path)
                if not parent_path:
                    return {"error": "Parent path is required"}
                res = await runtime.call_development_function(
                    create_folder, parent_path, new_name
                )
            else:
                file_path = input.get("path", "")
                if not file_path:
                    return {"error": "Path is required"}
                if not file_path.startswith("/"):
                    file_path = f"/{file_path}"
                res = await runtime.call_development_function(
                    rename_item, file_path, new_name
                )

            if res:
                result = await runtime.call_development_function(
                    get_work_dir_files.get_files, current_path
                )
                return {"data": result}

            error_msg = "Failed to create folder" if action == "create-folder" else "Rename failed"
            return {"error": error_msg}

        except Exception as e:
            return {"error": str(e)}


async def rename_item(file_path: str, new_name: str) -> bool:
    browser = FileBrowser()
    return browser.rename_item(file_path, new_name)


async def create_folder(parent_path: str, folder_name: str) -> bool:
    browser = FileBrowser()
    return browser.create_folder(parent_path, folder_name)
