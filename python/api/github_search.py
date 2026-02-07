from python.helpers.api import ApiHandler
from python.api.github_callback import get_github_auth
from flask import Request
import httpx


class GithubSearch(ApiHandler):
    """Search GitHub repositories"""

    async def process(self, input: dict, request: Request) -> dict:
        auth_data = get_github_auth()
        access_token = auth_data.get("access_token") if auth_data else None

        query = input.get("query", "")
        page = input.get("page", 1)
        per_page = input.get("per_page", 30)

        if not query:
            return {"error": "Search query is required"}

        headers = {"Accept": "application/vnd.github+json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": query,
                    "page": page,
                    "per_page": per_page,
                    "sort": "stars",
                    "order": "desc",
                },
                headers=headers,
            )

            if response.status_code != 200:
                return {"error": "Search failed", "status": response.status_code}

            search_data = response.json()

            return {
                "total_count": search_data.get("total_count", 0),
                "items": search_data.get("items", []),
                "page": page,
                "per_page": per_page,
            }
