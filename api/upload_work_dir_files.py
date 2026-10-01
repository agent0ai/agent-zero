import asyncio
import json
from werkzeug.datastructures import FileStorage
from helpers.api import ApiHandler, Request, Response
from helpers.file_browser import FileBrowser
from helpers.file_transfers import FileLimitExceeded
from helpers import files, runtime, extension
from api import get_work_dir_files
import os
import posixpath


class UploadWorkDirFiles(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        if "files[]" not in request.files:
            raise Exception("No files uploaded")

        current_path = request.form.get("path", "")
        uploaded_files = request.files.getlist("files[]")
        try:
            successful, failed = await upload_files(uploaded_files, current_path)
        except FileLimitExceeded as error:
            return Response(json.dumps({"error": str(error)}), status=413, mimetype="application/json")

        if not successful and failed:
            return {"error": "Files could not be uploaded. Check destination permissions and free disk space.",
                    "successful": [], "failed": failed}

        if successful:
            await extension.call_extensions_async(
                "workdir_file_mutation_after",
                agent=None,
                data={
                    "action": "upload",
                    "path": current_path,
                    "paths": [
                        posixpath.join(str(current_path).rstrip("/"), name)
                        for name in successful
                    ],
                    "current_path": current_path,
                },
            )

        # result = browser.get_files(current_path)
        result = await runtime.call_development_function(get_work_dir_files.get_files, current_path)

        return {
            "message": (
                "Files uploaded successfully"
                if not failed
                else "Some files failed to upload"
            ),
            "data": result,
            "successful": successful,
            "failed": failed,
        }


async def upload_files(uploaded_files: list[FileStorage], current_path: str):
    if runtime.is_development():
        successful = []
        failed = []
        for file in uploaded_files:
            base64_content = await asyncio.to_thread(FileBrowser.encode_upload, file)
            if await runtime.call_development_function(
                upload_file, current_path, file.filename, base64_content
            ):
                successful.append(file.filename)
            else:
                failed.append(file.filename)
    else:
        browser = FileBrowser()
        successful, failed = await asyncio.to_thread(browser.save_files, uploaded_files, current_path)

    return successful, failed


async def upload_file(current_path: str, filename: str, base64_content: str):
    browser = FileBrowser()
    return browser.save_file_b64(current_path, filename, base64_content)
