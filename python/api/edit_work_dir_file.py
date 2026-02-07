import mimetypes
import os

from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers.file_browser import FileBrowser
from python.helpers import runtime, files

MAX_EDIT_FILE_SIZE = 1024 * 1024
BINARY_SAMPLE_SIZE = 10 * 1024


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
            
            content_size = len(content.encode("utf-8"))
            if content_size > MAX_EDIT_FILE_SIZE:
                return {"error": "File exceeds 1 MB and cannot be edited"}
            
            res = await runtime.call_development_function(save_file, file_path, content)
            if not res:
                return {"error": "Failed to save file"}

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

    size = os.path.getsize(full_path)
    if size > MAX_EDIT_FILE_SIZE:
        raise Exception("File exceeds 1 MB and cannot be edited")

    # Binary detection: only sample the first ~10KB (per backend rules)
    if files.is_probably_binary_file(full_path, sample_size=BINARY_SAMPLE_SIZE):
        raise Exception("Binary file detected; editing is not supported")

    mime_type, _ = mimetypes.guess_type(full_path)
    try:
        with open(full_path, "r", encoding="utf-8", errors="strict") as file:
            content = file.read()
    except UnicodeDecodeError:
        raise Exception("Unable to decode file as UTF-8; editing is not supported")

    return {
        "path": file_path,
        "name": os.path.basename(full_path),
        "mime_type": mime_type or "text/plain",
        "content": content,
    }


def save_file(file_path: str, content: str) -> bool:
    browser = FileBrowser()
    return browser.save_text_file(file_path, content)
