from pathlib import Path

from helpers import socket_handlers


class PluginInstall(socket_handlers.JsonApiHandler):
    api_module = "plugins._plugin_installer.api.plugin_install"
    api_class = "PluginInstall"

    def validate(self, input: dict):
        if input.get("action") not in ("fetch_index", "check_compatibility", "install_git", "update_plugin", "install_zip"):
            raise socket_handlers.SocketError("INVALID_ARGUMENT", "Unknown installer action")
        if input.get("action") == "install_zip":
            path = input.get("zip_path")
            if not isinstance(path, str) or not Path(path).is_absolute() or not Path(path).is_file():
                raise socket_handlers.SocketError("INVALID_ARGUMENT", "zip_path must be an absolute local file path")

    async def invoke(self, input: dict):
        if input["action"] != "install_zip":
            return await super().invoke(input)
        from werkzeug.datastructures import FileStorage
        from plugins._plugin_installer.helpers.install import install_uploaded_zip

        # The upload helper copies the archive before extraction/cleanup, preserving the source.
        with open(input["zip_path"], "rb") as source:
            return install_uploaded_zip(FileStorage(source, filename=Path(input["zip_path"]).name))
