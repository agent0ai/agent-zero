import mimetypes
import os

from helpers.api import ApiHandler, Input, Output, Request
from helpers.file_browser import FileBrowser
from helpers import runtime, extension


class EditWorkDirFile(ApiHandler):
    @classmethod
    def get_methods(cls):
        return ["GET", "POST"]

    def _extract_error_message(self, error_str: str) -> str:
        """Extract user-friendly error message from exception string."""
        for line in reversed(error_str.split('\n')):
            if ': ' in line and ('Exception' in line or 'Error' in line):
                return line.split(': ', 1)[1].strip()
        return error_str.strip()

    async def process(self, input: Input, request: Request) -> Output:
        try:
            if request.method == "GET":
                file_path = request.args.get("path", "")
                if not file_path:
                    return {"error": "Path is required"}
                if not file_path.startswith("/"):
                    file_path = f"/{file_path}"

                data = await runtime.call_development_function(load_file, file_path)
                return {"data": data}

            file_path = input.get("path", "")
            if not file_path:
                return {"error": "Path is required"}
            if not file_path.startswith("/"):
                file_path = f"/{file_path}"

            content = input.get("content", "")
            if not isinstance(content, str):
                return {"error": "Content must be a string"}
            
            FileBrowser.text_bytes(content)
            
            res = await runtime.call_development_function(save_file, file_path, content)
            if not res:
                return {"error": "Failed to save file"}

            await extension.call_extensions_async(
                "workdir_file_mutation_after",
                agent=None,
                data={
                    "action": "edit",
                    "path": file_path,
                    "paths": [file_path],
                },
            )
            return {"ok": True}
        except Exception as e:
            # Extract clean error message from exception
            # RPC calls may return full tracebacks in exception strings
            return {"error": self._extract_error_message(str(e))}


async def load_file(file_path: str) -> dict:
    browser = FileBrowser()
    full_path = browser.get_full_path(file_path)

    if os.path.isdir(full_path):
        raise Exception("Path points to a directory")

    mime_type, _ = mimetypes.guess_type(full_path)
    with open(full_path, "rb") as file:
        content = FileBrowser.decode_text(file.read(FileBrowser.max_text_bytes() + 1))

    return {
        "path": file_path,
        "name": os.path.basename(full_path),
        "mime_type": mime_type or "text/plain",
        "content": content,
    }


def save_file(file_path: str, content: str) -> bool:
    browser = FileBrowser()
    return browser.save_text_file(file_path, content)
