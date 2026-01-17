from python.helpers import cowork
from python.helpers.api import ApiHandler, Request, Response


class CoworkApprovalsList(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context", "")
        try:
            context = self.use_context(ctxid, create_if_not_exists=False)
        except Exception:
            return {"approvals": []}

        approvals = cowork.get_approvals(context)
        return {"approvals": approvals}
