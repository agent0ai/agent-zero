from __future__ import annotations

from helpers import extension, runtime
from helpers.api import ApiHandler, Input, Output, Request
from api import get_work_dir_files


from helpers.file_archives import extract_archive


class ExtractWorkDirArchive(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        path = str(input.get("path") or "").strip()
        if not path:
            return {"error": "Archive path is required"}
        if not path.startswith("/"):
            path = f"/{path}"

        try:
            extracted_path = await runtime.call_development_function(extract_archive, path)
        except (OSError, ValueError) as exc:
            return {"error": str(exc)}

        current_path = str(input.get("currentPath") or "")
        await extension.call_extensions_async(
            "workdir_file_mutation_after",
            agent=None,
            data={
                "action": "extract",
                "path": extracted_path,
                "paths": [path, extracted_path],
                "current_path": current_path,
            },
        )
        listing = await runtime.call_development_function(get_work_dir_files.get_files, current_path)
        return {"data": listing, "extracted_path": extracted_path}
