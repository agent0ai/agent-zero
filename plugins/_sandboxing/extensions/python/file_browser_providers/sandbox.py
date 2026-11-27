from helpers.extension import Extension
from plugins._sandboxing.helpers.file_browser import SandboxFilesProvider


class SandboxFolders(Extension):
    def execute(self, providers, **kwargs):
        providers[SandboxFilesProvider.id] = SandboxFilesProvider()
