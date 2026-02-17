"""
Media file serving endpoint for audio and video files.
Supports range requests for seeking functionality.
"""
import os
import io
import base64
from python.helpers.api import ApiHandler, Request, Response, send_file
from python.helpers import files, runtime
from mimetypes import guess_type


class MediaGet(ApiHandler):
    """Serve media files (audio/video) with range request support for seeking."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        # Input data
        path = input.get("path", request.args.get("path", ""))
        
        if not path:
            raise ValueError("No path provided")

        # Get file extension and info
        file_ext = os.path.splitext(path)[1].lower()
        filename = os.path.basename(path)

        # Allowed media extensions
        audio_extensions = [".wav", ".mp3", ".ogg", ".flac", ".webm", ".m4a", ".aac"]
        video_extensions = [".mp4", ".webm", ".ogv", ".mov"]
        media_extensions = audio_extensions + video_extensions

        if file_ext not in media_extensions:
            raise ValueError(f"Unsupported media format: {file_ext}")

        # Determine media type
        is_audio = file_ext in audio_extensions
        
        # Check file existence and get content
        if runtime.is_development():
            if files.exists(path):
                file_content = files.read_file(path, "rb") if hasattr(files, 'read_file') else None
                if file_content is None:
                    # Use base64 method
                    b64_content = await runtime.call_development_function(
                        files.read_file_base64, path
                    )
                    file_content = base64.b64decode(b64_content)
            elif await runtime.call_development_function(files.exists, path):
                b64_content = await runtime.call_development_function(
                    files.read_file_base64, path
                )
                file_content = base64.b64decode(b64_content)
            else:
                raise ValueError(f"Media file not found: {path}")
        else:
            if files.exists(path):
                file_content = files.read_file(path, "rb") if hasattr(files, 'read_file') else None
                if file_content is None:
                    # Read file directly
                    with open(files.get_abs_path(path) if not os.path.isabs(path) else path, "rb") as f:
                        file_content = f.read()
            else:
                raise ValueError(f"Media file not found: {path}")

        # Get MIME type
        mime_type, _ = guess_type(filename)
        if not mime_type:
            mime_type = f"audio/{file_ext[1:]}" if is_audio else f"video/{file_ext[1:]}"

        # Get file size
        file_size = len(file_content) if isinstance(file_content, bytes) else os.path.getsize(path)

        # Handle range requests for seeking
        range_header = request.headers.get("range")

        if range_header:
            # Parse range header (e.g., "bytes=0-1023")
            try:
                range_match = range_header.replace("bytes=", "").split("-")
                start = int(range_match[0]) if range_match[0] else 0
                end = int(range_match[1]) if range_match[1] else file_size - 1
            except (ValueError, IndexError):
                start, end = 0, file_size - 1

            # Ensure valid range
            start = max(0, start)
            end = min(file_size - 1, end)
            content_length = end - start + 1

            # Create partial content
            if isinstance(file_content, bytes):
                partial_content = file_content[start:end+1]
                response = send_file(
                    io.BytesIO(partial_content),
                    mimetype=mime_type,
                    as_attachment=False,
                    download_name=filename,
                )
            else:
                response = send_file(
                    io.BytesIO(file_content[start:end+1]),
                    mimetype=mime_type,
                    as_attachment=False,
                    download_name=filename,
                )

            response.headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response.status_code = 206
        else:
            # Full file request
            if isinstance(file_content, bytes):
                response = send_file(
                    io.BytesIO(file_content),
                    mimetype=mime_type,
                    as_attachment=False,
                    download_name=filename,
                )
            else:
                response = send_file(
                    io.BytesIO(file_content),
                    mimetype=mime_type,
                    as_attachment=False,
                    download_name=filename,
                )

        # Add headers
        response.headers["Accept-Ranges"] = "bytes"
        response.headers["Content-Length"] = str(file_size if not range_header else content_length)
        response.headers["Cache-Control"] = "public, max-age=3600"
        response.headers["X-File-Type"] = "audio" if is_audio else "video"
        response.headers["X-File-Name"] = filename
        
        return response
