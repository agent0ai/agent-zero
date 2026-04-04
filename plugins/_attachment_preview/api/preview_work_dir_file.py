import base64
from io import BytesIO
import mimetypes
import os

from flask import Response
from helpers.api import ApiHandler, Input, Output, Request
from helpers import files, runtime
from api import file_info
from api.download_work_dir_file import fetch_file


# Previewable extensions
PREVIEWABLE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".svgz",
    ".pdf",
    ".mp4", ".webm", ".ogg", ".mov",
    ".mp3", ".wav", ".flac", ".aac", ".m4a",
    ".html", ".htm", ".md", ".txt", ".json", ".yaml", ".yml",
    ".xml", ".csv", ".log", ".ini", ".cfg", ".conf",
    ".py", ".js", ".ts", ".css", ".sh", ".bash", ".zsh",
    ".c", ".cpp", ".h", ".java", ".go", ".rs", ".rb",
    ".php", ".sql", ".r", ".lua", ".pl", ".swift", ".kt",
    ".toml", ".env", ".gitignore", ".dockerfile",
}


def stream_file_inline(file_source, filename, chunk_size=8192):
    if isinstance(file_source, str):
        file_size = os.path.getsize(file_source)
    elif isinstance(file_source, BytesIO):
        current_pos = file_source.tell()
        file_source.seek(0, 2)
        file_size = file_source.tell()
        file_source.seek(current_pos)
    else:
        raise ValueError(f"Unsupported file source type: {type(file_source)}")

    def generate():
        if isinstance(file_source, str):
            with open(file_source, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        elif isinstance(file_source, BytesIO):
            file_source.seek(0)
            while True:
                chunk = file_source.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    content_type, _ = mimetypes.guess_type(filename)
    if not content_type:
        content_type = 'application/octet-stream'

    headers = {
        'Content-Disposition': f'inline; filename="{filename}"',
        'Content-Length': str(file_size),
        'Cache-Control': 'no-cache',
        'X-Content-Type-Options': 'nosniff',
    }

    # Sandbox HTML
    if content_type in ('text/html', 'application/xhtml+xml'):
        headers['Content-Security-Policy'] = (
            "default-src 'none'; style-src 'unsafe-inline'; img-src data: blob:;"
        )

    return Response(
        generate(),
        content_type=content_type,
        direct_passthrough=True,
        headers=headers,
    )


class PreviewWorkDirFile(ApiHandler):

    @classmethod
    def get_methods(cls):
        return ["GET"]

    async def process(self, input: Input, request: Request) -> Output:
        file_path = request.args.get("path", input.get("path", ""))
        if not file_path:
            raise ValueError("No file path provided")
        if not file_path.startswith("/"):
            file_path = f"/{file_path}"

        # Validate extension
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in PREVIEWABLE_EXTENSIONS:
            raise ValueError(f"File type '{ext}' is not supported for preview")

        info = await runtime.call_development_function(
            file_info.get_file_info, file_path
        )

        if not info["exists"]:
            raise Exception(f"File {file_path} not found")
        if not info["is_file"]:
            raise Exception(f"Path {file_path} is not a file")

        filename = os.path.basename(info["file_name"])

        if runtime.is_development():
            b64 = await runtime.call_development_function(fetch_file, info["abs_path"])
            file_data = BytesIO(base64.b64decode(b64))
            return stream_file_inline(file_data, filename)
        else:
            return stream_file_inline(info["abs_path"], filename)
