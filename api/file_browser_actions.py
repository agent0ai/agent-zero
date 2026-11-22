import asyncio

from helpers import extension
from helpers.api import ApiHandler, Input, Output, Request
from helpers.file_browser_actions import change_permissions, compress, list_trash, properties, selection_size, trash_item


class FileBrowserActions(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action")
        try:
            if action == "list-trash":
                return {"entries": await asyncio.to_thread(list_trash)}
            paths = input.get("paths")
            if not isinstance(paths, list) or not paths or not all(isinstance(path, str) for path in paths):
                raise ValueError("Select at least one item.")
            if action == "properties":
                return {"entries": await asyncio.to_thread(properties, paths)}
            if action == "size":
                return {"size": await asyncio.to_thread(selection_size, paths)}
            current = input.get("currentPath", "")
            completed, failed = [], []
            if action == "compress":
                completed.append(await asyncio.to_thread(compress, paths, current, input.get("name")))
            elif action in ("trash", "restore", "purge", "chmod"):
                for path in dict.fromkeys(paths):
                    try:
                        if action == "chmod":
                            completed.append(await asyncio.to_thread(change_permissions, path, input.get("mode")))
                        else:
                            completed.append(await asyncio.to_thread(trash_item, action, path))
                    except (OSError, ValueError) as error:
                        failed.append(f"{path}: {error}")
            else:
                raise ValueError("Unknown file action.")
            if completed:
                await extension.call_extensions_async("workdir_file_mutation_after", agent=None, data={
                    "action": action, "path": completed[0], "paths": completed, "current_path": current,
                })
            return {"paths": completed, "failed": failed}
        except (OSError, ValueError, TypeError) as error:
            return {"error": str(error)}
