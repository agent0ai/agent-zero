from python.helpers.api import ApiHandler
from python.api.github_callback import get_github_auth
from flask import Request
import httpx


class GithubRepoDetail(ApiHandler):
    """Get detailed repository info"""

    async def process(self, input: dict, request: Request) -> dict:
        auth_data = get_github_auth()
        access_token = auth_data.get("access_token") if auth_data else None

        if not access_token:
            return {"error": "Not connected to GitHub", "connected": False}

        # Get params from input or query string
        owner = input.get("owner") or request.args.get("owner")
        repo = input.get("repo") or request.args.get("repo")

        if not owner or not repo:
            return {"error": "owner and repo parameters required"}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

        async with httpx.AsyncClient() as client:
            # Get repo info
            repo_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers,
            )

            if repo_response.status_code != 200:
                return {"error": "Repository not found", "status": 404}

            repo_data = repo_response.json()

            # Get branches
            branches_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/branches",
                params={"per_page": 100},
                headers=headers,
            )
            branches = branches_response.json() if branches_response.status_code == 200 else []

            # Get languages
            languages_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/languages",
                headers=headers,
            )
            languages = languages_response.json() if languages_response.status_code == 200 else {}

            return {
                "repository": {
                    "id": repo_data["id"],
                    "name": repo_data["name"],
                    "full_name": repo_data["full_name"],
                    "description": repo_data.get("description"),
                    "private": repo_data["private"],
                    "html_url": repo_data["html_url"],
                    "clone_url": repo_data["clone_url"],
                    "ssh_url": repo_data["ssh_url"],
                    "language": repo_data.get("language"),
                    "stargazers_count": repo_data["stargazers_count"],
                    "watchers_count": repo_data["watchers_count"],
                    "forks_count": repo_data["forks_count"],
                    "open_issues_count": repo_data["open_issues_count"],
                    "default_branch": repo_data["default_branch"],
                    "created_at": repo_data["created_at"],
                    "updated_at": repo_data["updated_at"],
                    "pushed_at": repo_data["pushed_at"],
                    "owner": {
                        "login": repo_data["owner"]["login"],
                        "avatar_url": repo_data["owner"]["avatar_url"],
                    },
                },
                "branches": [b["name"] for b in branches] if isinstance(branches, list) else [],
                "languages": languages,
            }
