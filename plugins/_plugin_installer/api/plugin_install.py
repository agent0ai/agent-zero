from __future__ import annotations

from helpers.api import ApiHandler, Input, Output, Request
from werkzeug.datastructures import FileStorage

from plugins._plugin_installer.helpers.install import (
    get_plugin_hub_index,
    install_from_git,
    install_uploaded_zip,
    update_from_git,
)

class PluginInstall(ApiHandler):
    """Plugin installation API. Handles ZIP upload, Git clone, and index fetch."""

    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "") or request.form.get("action", "")

        try:
            if action == "install_zip":
                return self._install_zip(request)
            elif action == "install_git":
                return self._install_git(input)
            elif action == "update_plugin":
                return self._update_git(input)
            elif action == "fetch_index":
                return self._fetch_index(input)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Installation failed: {e}"}

    def _install_zip(self, request: Request) -> dict:
        if "plugin_file" not in request.files:
            return {"success": False, "error": "No file provided"}

        plugin_file: FileStorage = request.files["plugin_file"]
        if not plugin_file.filename:
            return {"success": False, "error": "No file selected"}

        return install_uploaded_zip(plugin_file)

    def _install_git(self, input: dict) -> dict:
        git_url = (input.get("git_url", "") or "").strip()
        git_token = (input.get("git_token", "") or "").strip() or None
        plugin_name = input.get("plugin_name", "")
        thumbnail_url = (input.get("thumbnail_url") or "").strip()
        if not git_url:
            return {"success": False, "error": "Git URL is required"}

        return install_from_git(url=git_url, token=git_token, plugin_name=plugin_name, thumbnail_url=thumbnail_url)

    def _update_git(self, input: dict) -> dict:
        return update_from_git(input.get("plugin_name", ""))

    def _fetch_index(self, input: dict) -> dict:
        return {"success": True, **get_plugin_hub_index()}
