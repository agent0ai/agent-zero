"""Instance-wide File Browser preferences shared by local and remote editors."""
from helpers.api import ApiHandler, Request
from helpers.file_browser import FileBrowser
from helpers import settings


class FileBrowserSettings(ApiHandler):
    async def process(self, input: dict, request: Request):
        delta = {}
        for name, maximum in (("max_text_size_mb", 100), ("max_transfer_size_mb", None),
                              ("max_extract_size_mb", None), ("max_archive_entries", None)):
            if name not in input:
                continue
            limit = input[name]
            if type(limit) is not int or limit < 1 or (maximum is not None and limit > maximum):
                message = f"Enter a whole number from 1 to {maximum} MiB." if maximum else "Enter a positive whole number."
                return {"ok": False, "error": message}
            delta["file_browser_" + name] = limit
        if not delta:
            return {"ok": False, "error": "No size limit supplied."}
        settings.set_settings_delta(delta, apply=False)
        return {"ok": True, "limits": FileBrowser.limits()}
