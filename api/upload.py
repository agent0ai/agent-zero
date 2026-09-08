
from helpers.api import ApiHandler, Request, Response
from helpers import files
from helpers.security import safe_filename
from helpers.file_transfers import write_stream_atomic


def save_upload_atomic(file_storage, target_path, *, max_bytes=None):
    return write_stream_atomic(file_storage.stream, target_path, max_bytes=max_bytes)


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
                metadata = write_stream_atomic(
                    file.stream,
                    files.get_abs_path("usr/uploads", filename),
                )
                saved_filenames.append(filename)
                saved_files.append({"filename": filename, **metadata})

        return {"filenames": saved_filenames, "files": saved_files}


    def allowed_file(self,filename):
        return True
        # ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "txt", "pdf", "csv", "html", "json", "md"}
        # return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
