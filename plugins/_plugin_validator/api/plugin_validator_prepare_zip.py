from __future__ import annotations

import os
import time
import uuid
import zipfile
from pathlib import Path

from helpers import files
from helpers.api import ApiHandler, Input, Output, Request, Response
from plugins._plugin_installer.helpers.install import validate_plugin_dir
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def _find_plugin_root(extracted_dir: str) -> str:
    for root, _dirs, dir_files in os.walk(extracted_dir):
        if "plugin.yaml" in dir_files:
            return root
    raise ValueError("No plugin.yaml found in the uploaded archive")


class PluginValidatorPrepareZip(ApiHandler):
    """Extract an uploaded ZIP to a temp directory so the validator agent can inspect it."""

    async def process(self, input: Input, request: Request) -> Output:
        if "plugin_file" not in request.files:
            return Response("No file provided.", 400)

        plugin_file: FileStorage = request.files["plugin_file"]
        if not plugin_file.filename:
            return Response("No file selected.", 400)

        original_filename = Path((plugin_file.filename or "").strip()).name
        if not original_filename:
            return Response("No file selected.", 400)

        uploads_dir = Path(files.get_abs_path("tmp", "plugin_validation_uploads"))
        uploads_dir.mkdir(parents=True, exist_ok=True)

        safe_name = secure_filename(original_filename) or "plugin.zip"
        if not safe_name.lower().endswith(".zip"):
            safe_name = f"{safe_name}.zip"

        unique = uuid.uuid4().hex[:8]
        stamp = time.strftime("%Y%m%d_%H%M%S")
        upload_path = str(uploads_dir / f"plugin_{stamp}_{unique}_{safe_name}")
        extract_dir = files.get_abs_path(files.TEMP_DIR, "plugin_validation", f"tmp_plugin_{stamp}_{unique}")

        try:
            plugin_file.save(upload_path)
            files.create_dir_safe(extract_dir)

            with zipfile.ZipFile(upload_path, "r") as archive:
                for member in archive.namelist():
                    member_path = os.path.realpath(os.path.join(extract_dir, member))
                    if not files.is_in_dir(member_path, extract_dir):
                        raise ValueError(f"Unsafe path in archive: {member}")
                archive.extractall(extract_dir)

            plugin_root = _find_plugin_root(extract_dir)
            meta = validate_plugin_dir(plugin_root)

            return {
                "ok": True,
                "path": plugin_root,
                "cleanup_path": extract_dir,
                "plugin_name": meta.name,
                "title": meta.title or meta.name,
            }
        except ValueError as e:
            files.delete_dir(extract_dir)
            return Response(str(e), 400)
        except Exception as e:
            files.delete_dir(extract_dir)
            return Response(f"ZIP validation preparation failed: {e}", 500)
        finally:
            files.delete_file(upload_path)
