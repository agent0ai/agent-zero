"""Authenticated Files downloads; policy and I/O belong to shared helpers."""
import base64
import asyncio
from io import BytesIO
import json

from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers import files, runtime
from helpers.file_browser import prepare_files_download, prepare_files_response, remove_download_temporary, register_files_download
from helpers.file_transfers import stream_file_download, take_download_response, FileLimitExceeded


class DownloadFiles(ApiHandler):
    @classmethod
    def get_methods(cls):
        return ["GET", "POST"]

    async def process(self, input: Input, request: Request) -> Output:
        if request.method == "GET":
            try:
                return take_download_response(request.args.get("token", ""))
            except FileNotFoundError as error:
                return Response(json.dumps({"error": str(error)}), status=404, mimetype="application/json")
            except PermissionError as error:
                return Response(json.dumps({"error": str(error)}), status=403, mimetype="application/json")
        paths = input.get("paths", [])
        try:
            if runtime.is_development():
                download = await runtime.call_development_function(prepare_files_download, paths, input.get("currentPath", ""))
                try:
                    data = await runtime.call_development_function(files.read_file_base64, download["file_source"])
                finally:
                    if download["delete_after"]:
                        await runtime.call_development_function(remove_download_temporary, download["file_source"])
                download["file_source"] = BytesIO(base64.b64decode(data))
                download["delete_after"] = False
                response = await asyncio.to_thread(stream_file_download, **download)
                name = download["download_name"]
            else:
                response, name = await prepare_files_response(paths, input.get("currentPath", ""))
            token = register_files_download(response, paths)
            return {"download_url": "/api/download_work_dir_files?token=" + token, "name": name}
        except FileLimitExceeded as error:
            return Response(json.dumps({"error": str(error)}), status=413, mimetype="application/json")
        except (ValueError, FileNotFoundError, PermissionError) as error:
            return Response(json.dumps({"error": str(error)}), status=400, mimetype="application/json")
