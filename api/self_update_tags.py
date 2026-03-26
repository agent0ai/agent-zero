from helpers.api import ApiHandler, Request, Response

from helpers import runtime
from helpers import self_update


class SelfUpdateTags(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        branch = str(input.get("branch", "")).strip().lower()
        query = str(input.get("query", ""))
        current_branch = self_update.get_repo_version_info().get("branch", "").strip().lower()
        default_branch = current_branch if current_branch in self_update.SUPPORTED_BRANCHES else "main"

        try:
            tags, error = self_update.get_available_tags(
                branch or None,
                query=query,
            )
            return {
                "success": True,
                "supported": runtime.is_dockerized(),
                "branch": branch or default_branch,
                "query": query,
                "tags": tags,
                "error": error,
            }
        except Exception as e:
            return {
                "success": False,
                "supported": runtime.is_dockerized(),
                "branch": branch or "main",
                "query": query,
                "tags": [],
                "error": str(e),
            }
