from helpers.api import ApiHandler, Input, Output, Request, Response


from helpers.file_browser import FileBrowser
from helpers import extension
from api import get_work_dir_files


class DeleteWorkDirFile(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        try:
            file_path = input.get("path", "")
            if not file_path.startswith("/"):
                file_path = f"/{file_path}"

            current_path = input.get("currentPath", "")

            res = await delete_file(file_path)

            if res:
                await extension.call_extensions_async(
                    "workdir_file_mutation_after",
                    agent=None,
                    data={
                        "action": "delete",
                        "path": file_path,
                        "paths": [file_path],
                        "current_path": current_path,
                    },
                )
                # Get updated file list
                result = await get_work_dir_files.get_files(current_path)
                return {"data": result}
            else:
                return {"error": "File not found or could not be deleted"}
        except Exception as e:
            return {"error": str(e)}


async def delete_file(file_path: str):
    browser = FileBrowser()
    return browser.delete_file(file_path)
