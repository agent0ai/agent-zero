import base64
from io import BytesIO
import mimetypes
import os
from pathlib import Path

from flask import Response
from helpers.api import ApiHandler, Input, Output, Request
from helpers import files, runtime
from api import file_info
from urllib.parse import quote



def stream_file_download(file_source, download_name, chunk_size=8192):
    """
    Create a streaming response for file downloads that shows progress in browser.

    Args:
        file_source: Either a file path (str) or BytesIO object
        download_name: Name for the downloaded file
        chunk_size: Size of chunks to stream (default 8192 bytes)

    Returns:
        Flask Response object with streaming content
    """
    # Calculate file size for Content-Length header
    if isinstance(file_source, str):
        # File path - get size from filesystem
        file_size = os.path.getsize(file_source)
    elif isinstance(file_source, BytesIO):
        # BytesIO object - get size from buffer
        current_pos = file_source.tell()
        file_source.seek(0, 2)  # Seek to end
        file_size = file_source.tell()
        file_source.seek(current_pos)  # Restore original position
    else:
        raise ValueError(f"Unsupported file source type: {type(file_source)}")

    def generate():
        if isinstance(file_source, str):
            # File path - open and stream from disk
            with open(file_source, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        elif isinstance(file_source, BytesIO):
            # BytesIO object - stream from memory
            file_source.seek(0)  # Ensure we're at the beginning
            while True:
                chunk = file_source.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    # Detect content type based on file extension
    content_type, _ = mimetypes.guess_type(download_name)
    if not content_type:
        content_type = 'application/octet-stream'

    # Create streaming response with proper headers for immediate streaming
    response = Response(
        generate(),
        content_type=content_type,
        direct_passthrough=True,  # Prevent Flask from buffering the response
        headers={
            'Content-Disposition': make_disposition(download_name),
            'Content-Length': str(file_size),  # Critical for browser progress bars
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
            'Accept-Ranges': 'bytes'  # Allow browser to resume downloads
        }
    )

    return response


def make_disposition(download_name: str) -> str:
    # Basic ASCII fallback (strip or replace weird chars)
    ascii_fallback = download_name.encode("ascii", "ignore").decode("ascii") or "download"
    utf8_name = quote(download_name)  # URL-encode UTF-8 bytes

    # RFC 5987: filename* with UTF-8
    return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{utf8_name}'


def resolve_download_path(path: str) -> str:
    """Resolve a requested download path from the File Browser root."""
    base_dir = Path("/")
    candidate = Path(path)

    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (base_dir / candidate).resolve()

    try:
        resolved.relative_to(base_dir)
    except ValueError as exc:
        raise ValueError("Invalid file path") from exc

    return str(resolved)


class DownloadFile(ApiHandler):

    @classmethod
    def get_methods(cls):
        return ["GET"]

    async def process(self, input: Input, request: Request) -> Output:
        file_path = request.args.get("path", input.get("path", ""))
        if not file_path:
            raise ValueError("No file path provided")
        if not file_path.startswith("/"):
            file_path = f"/{file_path}"

        try:
            file_path = await runtime.call_development_function(
                resolve_download_path, file_path
            )
        except ValueError as exc:
            return Response(str(exc), status=400)

        file = await runtime.call_development_function(
            file_info.get_file_info, file_path
        )

        if not file["exists"]:
            raise Exception(f"File {file_path} not found")

        if file["is_dir"]:
            zip_file = await runtime.call_development_function(files.zip_dir, file["abs_path"])
            directory_name = os.path.basename(file_path.rstrip("/")) or "directory"
            download_name = f"{directory_name}.zip"
            if runtime.is_development():
                b64 = await runtime.call_development_function(fetch_file, zip_file)
                file_data = BytesIO(base64.b64decode(b64))
                return stream_file_download(
                    file_data,
                    download_name=download_name
                )
            else:
                return stream_file_download(
                    zip_file,
                    download_name=download_name
                )
        elif file["is_file"]:
            if runtime.is_development():
                b64 = await runtime.call_development_function(fetch_file, file["abs_path"])
                file_data = BytesIO(base64.b64decode(b64))
                return stream_file_download(
                    file_data,
                    download_name=os.path.basename(file_path)
                )
            else:
                return stream_file_download(
                    file["abs_path"],
                    download_name=os.path.basename(file["file_name"])
                )
        raise Exception(f"File {file_path} not found")


async def fetch_file(path):
    with open(path, "rb") as file:
        file_content = file.read()
        return base64.b64encode(file_content).decode("utf-8")
