import base64
import io
import os
from mimetypes import guess_type

from python.helpers import files, runtime
from python.helpers.api import ApiHandler, Request, Response, send_file


class ImageGet(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        # input data
        path = input.get("path", request.args.get("path", ""))
        _metadata = (
            input.get("metadata", request.args.get("metadata", "false")).lower()
            == "true"
        )

        if not path:
            raise ValueError("No path provided")

        # Validate path to prevent directory traversal
        if "\x00" in path:
            raise ValueError("Invalid path")

        if runtime.is_development():
            real_path = os.path.realpath(files.fix_dev_path(path))
        else:
            real_path = os.path.realpath(path)

        if not files.is_in_base_dir(real_path) and not files.is_in_dir(
            real_path, "/root"
        ):
            raise ValueError("Path is outside of allowed directory")

        # get file extension and info
        file_ext = os.path.splitext(real_path)[1].lower()
        filename = os.path.basename(real_path)

        # list of allowed image extensions
        image_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".svg",
            ".ico",
            ".svgz",
        ]

        # # If metadata is requested, return file information
        # if metadata:
        #     return _get_file_metadata(path, filename, file_ext, image_extensions)

        if file_ext in image_extensions:
            # in development environment, try to serve the image from local file system if exists, otherwise from docker
            if runtime.is_development():
                if files.exists(real_path):
                    response = send_file(real_path)
                elif await runtime.call_development_function(files.exists, path):
                    b64_content = await runtime.call_development_function(
                        files.read_file_base64, path
                    )
                    file_content = base64.b64decode(b64_content)
                    mime_type, _ = guess_type(filename)
                    if not mime_type:
                        mime_type = "application/octet-stream"
                    response = send_file(
                        io.BytesIO(file_content),
                        mimetype=mime_type,
                        as_attachment=False,
                        download_name=filename,
                    )
                else:
                    response = _send_fallback_icon("image")
            else:
                if files.exists(real_path):
                    response = send_file(real_path)
                else:
                    response = _send_fallback_icon("image")

            # Add cache headers for better device sync performance
            response.headers["Cache-Control"] = "public, max-age=3600"
            response.headers["X-File-Type"] = "image"
            response.headers["X-File-Name"] = filename
            return response
        else:
            # Handle non-image files with fallback icons
            return _send_file_type_icon(file_ext, filename)


def _send_file_type_icon(file_ext, filename=None):
    """Return appropriate icon for file type"""

    # Map file extensions to icon names
    icon_mapping = {
        # Archive files
        ".zip": "archive",
        ".rar": "archive",
        ".7z": "archive",
        ".tar": "archive",
        ".gz": "archive",
        # Document files
        ".pdf": "document",
        ".doc": "document",
        ".docx": "document",
        ".txt": "document",
        ".rtf": "document",
        ".odt": "document",
        # Code files
        ".py": "code",
        ".js": "code",
        ".html": "code",
        ".css": "code",
        ".json": "code",
        ".xml": "code",
        ".md": "code",
        ".yml": "code",
        ".yaml": "code",
        ".sql": "code",
        ".sh": "code",
        ".bat": "code",
        # Spreadsheet files
        ".xls": "document",
        ".xlsx": "document",
        ".csv": "document",
        # Presentation files
        ".ppt": "document",
        ".pptx": "document",
        ".odp": "document",
    }

    # Get icon name, default to 'file' if not found
    icon_name = icon_mapping.get(file_ext, "file")

    response = _send_fallback_icon(icon_name)

    # Add headers for device sync
    if hasattr(response, "headers"):
        response.headers["Cache-Control"] = (
            "public, max-age=86400"  # Cache icons for 24 hours
        )
        response.headers["X-File-Type"] = "icon"
        response.headers["X-Icon-Type"] = icon_name
        if filename:
            response.headers["X-File-Name"] = filename

    return response


def _send_fallback_icon(icon_name):
    """Return fallback icon from public directory"""

    # Path to public icons
    icon_path = files.get_abs_path(f"webui/public/{icon_name}.svg")

    # Check if specific icon exists, fallback to generic file icon
    if not os.path.exists(icon_path):
        icon_path = files.get_abs_path("webui/public/file.svg")

    # Final fallback if file.svg doesn't exist
    if not os.path.exists(icon_path):
        raise ValueError(f"Fallback icon not found: {icon_path}")

    return send_file(icon_path, mimetype="image/svg+xml")
