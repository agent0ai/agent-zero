import asyncio

from helpers.extension import Extension
from plugins._browser.helpers.extension_uploads import record_user_attachments


class RememberBrowserUploadSources(Extension):
    async def execute(self, data: dict, **kwargs):
        if self.agent and isinstance(data, dict):
            await asyncio.to_thread(record_user_attachments, self.agent.context, data.get("attachment_paths"))
