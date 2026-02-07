from python.helpers.api import ApiHandler
from python.api.github_callback import get_github_auth
from flask import Request
import httpx


class GithubRepos(ApiHandler):
    """List GitHub repositories"""

    async def process(self, input: dict, request: Request) -> dict:
        auth_data = get_github_auth()
        access_token = auth_data.get("access_token") if auth_data else None

        if not access_token:
            return {"error": "Not connected to GitHub", "connected": False}

        # Get params from input (POST body) or query string
        page = input.get("page") or request.args.get("page", 1, type=int)
        per_page = input.get("per_page") or request.args.get("per_page", 30, type=int)
        sort = input.get("sort") or request.args.get("sort", "updated")
        direction = input.get("direction") or request.args.get("direction", "desc")
        type_filter = input.get("type") or request.args.get("type", "all")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/repos",
                params={
                    "page": page,
                    "per_page": per_page,
                    "sort": sort,
                    "direction": direction,
                    "type": type_filter,
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )

            if response.status_code != 200:
                return {"error": "Failed to fetch repositories", "status": response.status_code}

            repos = response.json()

            # Parse Link header for pagination
            link_header = response.headers.get("Link", "")
            has_next = 'rel="next"' in link_header
            has_prev = 'rel="prev"' in link_header

            return {
                "repositories": [
                    {
                        "id": repo["id"],
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description"),
                        "private": repo["private"],
                        "html_url": repo["html_url"],
                        "language": repo.get("language"),
                        "stargazers_count": repo["stargazers_count"],
                        "forks_count": repo["forks_count"],
                        "updated_at": repo["updated_at"],
                        "default_branch": repo["default_branch"],
                        "owner": {
                            "login": repo["owner"]["login"],
                            "avatar_url": repo["owner"]["avatar_url"],
                        },
                    }
                    for repo in repos
                ],
                "page": page,
                "per_page": per_page,
                "has_next": has_next,
                "has_prev": has_prev,
            }
