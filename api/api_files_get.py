import base64
import os
from helpers.api import ApiHandler, Request, Response
from helpers import files
from helpers.print_style import PrintStyle
import json


class ApiFilesGet(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # Get paths from input
            paths = input.get("paths", [])

            if not paths:
                return Response(
                    '{"error": "paths array is required"}',
                    status=400,
                    mimetype="application/json"
                )

            if not isinstance(paths, list):
                return Response(
                    '{"error": "paths must be an array"}',
                    status=400,
                    mimetype="application/json"
                )

            result = {}

            for path in paths:
                try:
                    # CVE-2026-4307: `path` comes from the request body, so it is never
                    # trusted. Only /a0/... paths are addressable, each is resolved through
                    # the containment check, and the old "assume it's already an
                    # external/absolute path" branch -- which read ANY file on disk and
                    # returned it base64-encoded -- is gone.
                    if not isinstance(path, str) or not path.startswith("/a0/"):
                        PrintStyle.warning(
                            f"Refused path outside the Agent Zero directory: {path}"
                        )
                        continue
                    if path.startswith("/a0/tmp/uploads/"):
                        relative_path = os.path.join(
                            "usr/uploads", path.replace("/a0/tmp/uploads/", "", 1)
                        )
                    else:
                        relative_path = path.replace("/a0/", "", 1)
                    try:
                        external_path = files.get_abs_path_contained(relative_path)
                    except files.PathEscapesBaseDirError as exc:
                        PrintStyle.warning(f"Refused traversal attempt: {exc}")
                        continue
                    filename = os.path.basename(external_path)

                    # Check if file exists
                    if not os.path.exists(external_path):
                        PrintStyle.warning(f"File not found: {path}")
                        continue

                    # Read and encode file
                    with open(external_path, "rb") as f:
                        file_content = f.read()
                        base64_content = base64.b64encode(file_content).decode('utf-8')
                        result[filename] = base64_content

                    PrintStyle().print(f"Retrieved file: {filename} ({len(file_content)} bytes)")

                except Exception as e:
                    PrintStyle.error(f"Failed to read file {path}: {str(e)}")
                    continue

            # Log the retrieval
            PrintStyle(
                background_color="#2ECC71", font_color="white", bold=True, padding=True
            ).print(f"API Files retrieved: {len(result)} files")

            return result

        except Exception as e:
            PrintStyle.error(f"API files get error: {str(e)}")
            return Response(
                json.dumps({"error": f"Internal server error: {str(e)}"}),
                status=500,
                mimetype="application/json"
            )
