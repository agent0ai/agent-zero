from python.helpers.api import ApiHandler
from python.api.github_callback import get_github_auth
from flask import Request
import httpx


class GithubContents(ApiHandler):
    """Get repository contents (file browser)"""

    async def process(self, input: dict, request: Request) -> dict:
        auth_data = get_github_auth()
        access_token = auth_data.get("access_token") if auth_data else None

        if not access_token:
            return {"error": "Not connected to GitHub", "connected": False}

        # Get params from input or query string
        owner = input.get("owner") or request.args.get("owner")
        repo = input.get("repo") or request.args.get("repo")
        path = input.get("path") or request.args.get("path", "")
        ref = input.get("ref") or request.args.get("ref", "")

        if not owner or not repo:
            return {"error": "owner and repo parameters required"}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

        params = {}
        if ref:
            params["ref"] = ref

        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            response = await client.get(url, params=params, headers=headers)

            if response.status_code != 200:
                return {"error": "Failed to fetch contents", "status": response.status_code}

            data = response.json()

            # Handle single file vs directory
            if isinstance(data, dict):
                # Single file
                return {
                    "type": "file",
                    "content": {
                        "name": data["name"],
                        "path": data["path"],
                        "sha": data["sha"],
                        "size": data["size"],
                        "type": data["type"],
                        "content": data.get("content"),  # Base64 encoded
                        "encoding": data.get("encoding"),
                        "html_url": data["html_url"],
                        "download_url": data.get("download_url"),
                    },
                }
            else:
                # Directory listing
                return {
                    "type": "directory",
                    "path": path,
                    "contents": [
                        {
                            "name": item["name"],
                            "path": item["path"],
                            "sha": item["sha"],
                            "size": item.get("size", 0),
                            "type": item["type"],
                            "html_url": item["html_url"],
                            "download_url": item.get("download_url"),
                        }
                        for item in sorted(data, key=lambda x: (x["type"] != "dir", x["name"].lower()))
                    ],
                }
