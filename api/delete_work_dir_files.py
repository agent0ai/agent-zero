from helpers.api import ApiHandler, Input, Output, Request
from helpers.file_browser import FileBrowser
from helpers import runtime, extension
from api import get_work_dir_files
from helpers.file_archives import normalize_paths


class DeleteWorkDirFiles(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        try:
            paths = normalize_paths(input.get("paths", []))
        except ValueError as exc:
            return {"error": str(exc)}

        current_path = input.get("currentPath", "")

        if not paths:
            return {"error": "No file paths provided"}

        result = await runtime.call_development_function(delete_files, paths)
        deleted = result["deleted"]
        failed = result["failed"]

        if deleted:
            await extension.call_extensions_async(
                "workdir_file_mutation_after",
                agent=None,
                data={
                    "action": "bulk_delete",
                    "path": deleted[0],
                    "paths": deleted,
                    "current_path": current_path,
                },
            )

        files_result = await runtime.call_development_function(
            get_work_dir_files.get_files, current_path
        )

        if not deleted:
            return {
                "error": "Selected items could not be deleted",
                "data": files_result,
                "deleted": deleted,
                "failed": failed,
            }

        return {
            "data": files_result,
            "deleted": deleted,
            "failed": failed,
        }


async def delete_files(paths: list[str]) -> dict:
    browser = FileBrowser()
    deleted: list[str] = []
    failed: list[str] = []

    for path in collapse_nested_paths(paths):
        if path == "/":
            failed.append(path)
            continue

        if browser.delete_file(path):
            deleted.append(path)
        else:
            failed.append(path)

    return {"deleted": deleted, "failed": failed}


def collapse_nested_paths(paths: list[str]) -> list[str]:
    collapsed: list[str] = []
    for path in sorted(normalize_paths(paths), key=lambda item: item.count("/")):
        clean_path = "/" + path.strip("/")
        if any(
            clean_path == parent or clean_path.startswith(parent.rstrip("/") + "/")
            for parent in collapsed
        ):
            continue
        collapsed.append(clean_path)
    return collapsed
