"""Receive a requested host file into its short-lived, server-owned transfer slot."""
import asyncio

from helpers.api import ApiHandler, Request
from plugins._a0_connector.helpers.file_browser import receive_upload


class FileBrowserTransfer(ApiHandler):
    async def process(self, input: dict, request: Request):
        storage = request.files.get("file")
        if storage is None:
            return {"ok": False, "error": "File is required."}
        try:
            return await asyncio.to_thread(receive_upload, request.args.get("transfer_token", ""), storage)
        except (ValueError, PermissionError) as error:
            return {"ok": False, "error": str(error)}
