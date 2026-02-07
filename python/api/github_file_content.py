from python.helpers.api import ApiHandler
from python.api.github_callback import get_github_auth
from flask import Request
import httpx
import base64


class GithubFileContent(ApiHandler):
    """Get file content from a repository"""

    async def process(self, input: dict, request: Request) -> dict:
        auth_data = get_github_auth()
        access_token = auth_data.get("access_token") if auth_data else None

        if not access_token:
            return {"error": "Not connected to GitHub", "connected": False}

        owner = input.get("owner", "")
        repo = input.get("repo", "")
        path = input.get("path", "")
        ref = input.get("ref", "")

        if not owner or not repo or not path:
            return {"error": "Owner, repo, and path are required"}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

        params = {}
        if ref:
            params["ref"] = ref

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                headers=headers,
                params=params,
            )

            if response.status_code != 200:
                return {"error": "Failed to fetch file", "status": response.status_code}

            file_data = response.json()

            if isinstance(file_data, dict) and file_data.get("type") == "file":
                content = file_data.get("content", "")
                if content:
                    try:
                        decoded = base64.b64decode(content).decode("utf-8")
                        file_data["decoded_content"] = decoded
                    except Exception:
                        file_data["decoded_content"] = None

            return file_data
