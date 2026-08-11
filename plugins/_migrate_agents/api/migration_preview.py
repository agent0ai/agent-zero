from __future__ import annotations

from helpers.api import ApiHandler, Input, Output, Request, Response
from plugins._migrate_agents.helpers.migration import MAX_TOTAL_BYTES, Upload, parse_bundle, preview


def uploaded_files(request: Request) -> list[Upload]:
    result: list[Upload] = []
    total = 0
    for item in request.files.getlist("files[]"):
        data = item.stream.read(MAX_TOTAL_BYTES + 1)
        total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise ValueError("Upload exceeds the 256 MiB limit")
        result.append(Upload(item.filename or "upload", data))
    if not result:
        raise ValueError("Choose at least one export file or folder")
    return result


class MigrationPreview(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        try:
            source = str(request.form.get("source") or "").strip().lower()
            return preview(parse_bundle(source, uploaded_files(request)))
        except ValueError as exc:
            return Response(str(exc), 400)
