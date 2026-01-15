from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files
from python.helpers.settings import set_settings_delta


class CoworkFoldersSet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        raw_paths = input.get("paths", [])
        if not isinstance(raw_paths, list):
            raw_paths = []

        normalized: list[str] = []
        seen = set()
        for path in raw_paths:
            if not isinstance(path, str):
                continue
            cleaned = path.strip()
            if not cleaned:
                continue
            normalized_path = files.normalize_a0_path(files.fix_dev_path(cleaned))
            if normalized_path == "/a0/.":
                normalized_path = "/a0"
            if normalized_path not in seen:
                normalized.append(normalized_path)
                seen.add(normalized_path)

        set_settings_delta({"cowork_allowed_paths": normalized})
        return {"paths": normalized}
