from helpers.api import ApiHandler, Request, Response
from helpers.file_browser import FileBrowser
from helpers import runtime, files

class GetWorkDirFiles(ApiHandler):

    @classmethod
    def get_methods(cls):
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        if request.args.get("limits") == "1":
            return {"limits": FileBrowser.limits()}
        current_path = request.args.get("path", "") or "$WORK_DIR"
        if current_path == "$WORK_DIR":
            # if runtime.is_development():
            #     current_path = "work_dir"
            # else:
            #     current_path = "root"
            current_path = "/a0"

        # browser = FileBrowser()
        # result = browser.get_files(current_path)
        result = await runtime.call_development_function(get_files, current_path)

        return {"data": result, "limits": FileBrowser.limits()}


async def get_files(path):
    from helpers import file_connections
    if file_connections.is_remote(path):
        import asyncio
        return await asyncio.to_thread(file_connections.listing, path)
    browser = FileBrowser()
    return browser.get_files(path)
