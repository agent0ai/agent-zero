from python.helpers.extension import Extension
from python.helpers.langfuse_helper import get_langfuse_client


class LangfuseInit(Extension):

    async def execute(self, **kwargs):
        get_langfuse_client()
