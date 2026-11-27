"""Authenticated Files downloads; policy and I/O belong to shared helpers."""
import json

from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers.file_browser import prepare_files_response, register_files_download
from helpers.file_transfers import take_download_response, FileLimitExceeded


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
            response, name = await prepare_files_response(paths, input.get("currentPath", ""))
            token = register_files_download(response, paths)
            return {"download_url": "/api/download_work_dir_files?token=" + token, "name": name}
        except FileLimitExceeded as error:
            return Response(json.dumps({"error": str(error)}), status=413, mimetype="application/json")
        except (ValueError, FileNotFoundError, PermissionError) as error:
            return Response(json.dumps({"error": str(error)}), status=400, mimetype="application/json")
