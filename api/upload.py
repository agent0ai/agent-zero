import hashlib
import os
import tempfile
from typing import Any

from helpers.api import ApiHandler, Request, Response
from helpers import files
from helpers.security import safe_filename


_UPLOAD_CHUNK_BYTES = 1024 * 1024


def save_upload_atomic(file_storage: Any, target_path: str) -> dict[str, Any]:
    directory = os.path.dirname(target_path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".partial-", dir=directory)
    digest = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(fd, "wb") as handle:
            while chunk := file_storage.stream.read(_UPLOAD_CHUNK_BYTES):
                handle.write(chunk)
                digest.update(chunk)
                size += len(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target_path)
        try:
            directory_fd = os.open(directory, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
    return {"size": size, "sha256": digest.hexdigest()}


class UploadFile(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        if "file" not in request.files:
            raise Exception("No file part")

        file_list = request.files.getlist("file")  # Handle multiple files
        saved_filenames = []
        saved_files = []

        for file in file_list:
            if file and self.allowed_file(file.filename):  # Check file type
                if not file.filename:
                    continue
                filename = safe_filename(file.filename)
                if not filename:
                    continue
                metadata = save_upload_atomic(
                    file,
                    files.get_abs_path("usr/uploads", filename),
                )
                saved_filenames.append(filename)
                saved_files.append({"filename": filename, **metadata})

        return {"filenames": saved_filenames, "files": saved_files}


    def allowed_file(self,filename):
        return True
        # ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "txt", "pdf", "csv", "html", "json", "md"}
        # return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
