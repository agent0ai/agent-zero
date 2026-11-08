from helpers.api import ApiHandler, Request, Response
from helpers.file_browser import FileBrowser
from helpers import files

class GetWorkDirFiles(ApiHandler):

    @classmethod
    def get_methods(cls):
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        if request.args.get("limits") == "1":
            return {"limits": FileBrowser.limits()}
        current_path = request.args.get("path", "") or "$WORK_DIR"
        if current_path == "$WORK_DIR":
            current_path = "/a0"

        result = await get_files(current_path)

        return {"data": result, "limits": FileBrowser.limits()}


async def get_files(path):
    from helpers import file_connections
    if file_connections.is_remote(path):
        import asyncio
        return await asyncio.to_thread(file_connections.listing, path)
    browser = FileBrowser()
    return browser.get_files(files.fix_dev_path(str(browser.base_dir / path)))
