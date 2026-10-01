import base64
from io import BytesIO
import os
from pathlib import Path

from flask import Response
from helpers.api import ApiHandler, Input, Output, Request
from helpers import files, runtime, file_archives
from api import file_info


from helpers.file_transfers import stream_file_download


def resolve_download_path(path: str) -> str:
    """Resolve a requested download path from the File Browser root."""
    return str(file_archives.resolve_download_path(path, Path("/")))


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
                try:
                    b64 = await runtime.call_development_function(files.read_file_base64, zip_file)
                finally:
                    await runtime.call_development_function(files.delete_file, zip_file)
                file_data = BytesIO(base64.b64decode(b64))
                return stream_file_download(
                    file_data,
                    download_name=download_name
                )
            else:
                try:
                    return stream_file_download(zip_file, download_name=download_name, delete_after=True)
                except BaseException:
                    files.delete_file(zip_file)
                    raise
        elif file["is_file"]:
            if runtime.is_development():
                b64 = await runtime.call_development_function(files.read_file_base64, file["abs_path"])
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
