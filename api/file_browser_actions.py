import asyncio

from helpers import extension
from helpers.api import ApiHandler, Input, Output, Request
from helpers.file_browser_actions import compress, list_trash, trash_item


class FileBrowserActions(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action")
        try:
            if action == "list-trash":
                return {"entries": await asyncio.to_thread(list_trash)}
            paths = input.get("paths")
            if not isinstance(paths, list) or not paths or not all(isinstance(path, str) for path in paths):
                raise ValueError("Select at least one item.")
            current = input.get("currentPath", "")
            completed, failed = [], []
            if action == "compress":
                completed.append(await asyncio.to_thread(compress, paths, current, input.get("name")))
            elif action in ("trash", "restore", "purge"):
                for path in dict.fromkeys(paths):
                    try:
                        completed.append(await asyncio.to_thread(trash_item, action, path))
                    except (OSError, ValueError) as error:
                        failed.append(str(error))
            else:
                raise ValueError("Unknown file action.")
            if completed:
                await extension.call_extensions_async("workdir_file_mutation_after", agent=None, data={
                    "action": action, "path": completed[0], "paths": completed, "current_path": current,
                })
            return {"paths": completed, "failed": failed}
        except (OSError, ValueError, TypeError) as error:
            return {"error": str(error)}
