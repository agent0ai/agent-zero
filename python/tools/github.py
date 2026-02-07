import httpx
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.api.github_callback import get_github_auth


class Github(Tool):
    """Tool for interacting with GitHub repositories."""

    async def execute(self, action="", **kwargs) -> Response:
        auth_data = get_github_auth()
        if not auth_data:
            return Response(
                message="GitHub is not connected. Ask the user to connect to GitHub in Settings > GitHub.",
                break_loop=False,
            )

        access_token = auth_data.get("access_token")
        if not access_token:
            return Response(
                message="GitHub authentication is incomplete. Ask the user to reconnect.",
                break_loop=False,
            )

        # Route to appropriate method based on action
        if action == "list_repos":
            result = await self.list_repos(access_token, **kwargs)
        elif action == "get_repo":
            result = await self.get_repo(access_token, **kwargs)
        elif action == "get_contents":
            result = await self.get_contents(access_token, **kwargs)
        elif action == "get_file":
            result = await self.get_file(access_token, **kwargs)
        elif action == "search_repos":
            result = await self.search_repos(access_token, **kwargs)
        else:
            result = f"Unknown action: {action}. Valid actions: list_repos, get_repo, get_contents, get_file, search_repos"

        await self.agent.handle_intervention(result)
        return Response(message=result, break_loop=False)

    async def list_repos(self, token: str, page: int = 1, per_page: int = 30, **kwargs) -> str:
        """List user's repositories."""
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/repos",
                params={"page": page, "per_page": per_page, "sort": "updated"},
                headers=headers,
            )

            if response.status_code != 200:
                return f"Failed to fetch repositories: HTTP {response.status_code}"

            repos = response.json()
            if not repos:
                return "No repositories found."

            lines = ["**Your GitHub Repositories:**\n"]
            for repo in repos:
                visibility = "Private" if repo["private"] else "Public"
                desc = repo.get("description") or "No description"
                lines.append(
                    f"- **{repo['full_name']}** ({visibility})\n"
                    f"  {desc}\n"
                    f"  Stars: {repo['stargazers_count']} | "
                    f"Language: {repo.get('language') or 'N/A'}"
                )

            return "\n".join(lines)

    async def get_repo(self, token: str, owner: str = "", repo: str = "", **kwargs) -> str:
        """Get detailed info about a repository."""
        if not owner or not repo:
            return "Error: 'owner' and 'repo' arguments are required."

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers,
            )

            if response.status_code == 404:
                return f"Repository {owner}/{repo} not found."
            if response.status_code != 200:
                return f"Failed to fetch repository: HTTP {response.status_code}"

            data = response.json()
            visibility = "Private" if data["private"] else "Public"

            return (
                f"**{data['full_name']}** ({visibility})\n\n"
                f"**Description:** {data.get('description') or 'No description'}\n\n"
                f"**Stats:**\n"
                f"- Stars: {data['stargazers_count']}\n"
                f"- Forks: {data['forks_count']}\n"
                f"- Watchers: {data['watchers_count']}\n"
                f"- Open Issues: {data['open_issues_count']}\n\n"
                f"**Details:**\n"
                f"- Language: {data.get('language') or 'N/A'}\n"
                f"- Default Branch: {data['default_branch']}\n"
                f"- Created: {data['created_at']}\n"
                f"- Updated: {data['updated_at']}\n"
                f"- URL: {data['html_url']}"
            )

    async def get_contents(
        self, token: str, owner: str = "", repo: str = "", path: str = "", **kwargs
    ) -> str:
        """List contents of a directory in a repository."""
        if not owner or not repo:
            return "Error: 'owner' and 'repo' arguments are required."

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            response = await client.get(url, headers=headers)

            if response.status_code == 404:
                return f"Path '{path}' not found in {owner}/{repo}."
            if response.status_code != 200:
                return f"Failed to fetch contents: HTTP {response.status_code}"

            data = response.json()

            # Single file
            if isinstance(data, dict):
                return f"'{path}' is a file. Use action='get_file' to read its contents."

            # Directory listing
            lines = [f"**Contents of {owner}/{repo}/{path or '(root)'}:**\n"]

            # Sort: directories first, then files
            items = sorted(data, key=lambda x: (x["type"] != "dir", x["name"].lower()))

            for item in items:
                icon = "[DIR]" if item["type"] == "dir" else "[FILE]"
                size = f" ({item.get('size', 0)} bytes)" if item["type"] == "file" else ""
                lines.append(f"- {icon} {item['name']}{size}")

            return "\n".join(lines)

    async def get_file(
        self, token: str, owner: str = "", repo: str = "", path: str = "", **kwargs
    ) -> str:
        """Get the contents of a file from a repository."""
        if not owner or not repo or not path:
            return "Error: 'owner', 'repo', and 'path' arguments are required."

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            response = await client.get(url, headers=headers)

            if response.status_code == 404:
                return f"File '{path}' not found in {owner}/{repo}."
            if response.status_code != 200:
                return f"Failed to fetch file: HTTP {response.status_code}"

            data = response.json()

            if isinstance(data, list):
                return f"'{path}' is a directory. Use action='get_contents' to list its contents."

            if data.get("type") != "file":
                return f"'{path}' is not a file (type: {data.get('type')})."

            # Decode base64 content
            import base64
            try:
                content = base64.b64decode(data.get("content", "")).decode("utf-8")
            except Exception as e:
                return f"Could not decode file content: {e}"

            # Truncate very large files
            max_chars = 50000
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n\n... [truncated, file is {len(content)} characters]"

            return (
                f"**File: {owner}/{repo}/{path}**\n"
                f"Size: {data.get('size', 0)} bytes\n\n"
                f"```\n{content}\n```"
            )

    async def search_repos(self, token: str, query: str = "", **kwargs) -> str:
        """Search GitHub repositories."""
        if not query:
            return "Error: 'query' argument is required."

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "per_page": 10, "sort": "stars"},
                headers=headers,
            )

            if response.status_code != 200:
                return f"Search failed: HTTP {response.status_code}"

            data = response.json()
            repos = data.get("items", [])

            if not repos:
                return f"No repositories found for '{query}'."

            lines = [f"**Search results for '{query}'** ({data.get('total_count', 0)} total):\n"]
            for repo in repos:
                visibility = "Private" if repo["private"] else "Public"
                desc = repo.get("description") or "No description"
                lines.append(
                    f"- **{repo['full_name']}** ({visibility})\n"
                    f"  {desc[:100]}{'...' if len(desc) > 100 else ''}\n"
                    f"  Stars: {repo['stargazers_count']} | Language: {repo.get('language') or 'N/A'}"
                )

            return "\n".join(lines)
