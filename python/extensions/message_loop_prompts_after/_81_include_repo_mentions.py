from python.helpers.extension import Extension
from agent import LoopData
import httpx


class IncludeRepoMentions(Extension):
    """Inject @mentioned GitHub repository context into agent prompts."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Import here to avoid circular imports
        from python.api.github_callback import get_github_auth

        # Get mentions from agent.data (set by hist_add_user_message)
        all_mentions = self.agent.data.get("mentions", [])
        mentions = [m for m in all_mentions if m.get("type") == "repo"]
        # Legacy fallback
        if not mentions:
            mentions = self.agent.data.get("repo_mentions", [])
        if not mentions:
            return

        auth_data = get_github_auth()
        if not auth_data:
            return  # Not connected to GitHub

        access_token = auth_data.get("access_token")
        if not access_token:
            return

        # Process each mention and inject context
        for mention in mentions:
            owner = mention.get("owner")
            repo = mention.get("repo")
            if not owner or not repo:
                continue

            context = await self.build_repo_context(access_token, owner, repo)
            if context:
                key = f"repo_mention_{owner}_{repo}"
                loop_data.extras_temporary[key] = context

    async def build_repo_context(
        self, token: str, owner: str, repo: str
    ) -> str | None:
        """Fetch repo metadata, file tree, and README from GitHub API."""
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        try:
            async with httpx.AsyncClient() as client:
                # Fetch repo metadata
                repo_response = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}",
                    headers=headers,
                )
                if repo_response.status_code != 200:
                    return None

                repo_data = repo_response.json()
                default_branch = repo_data.get("default_branch", "main")

                # Fetch file tree
                tree_response = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1",
                    headers=headers,
                )

                file_tree = ""
                tree_items = []
                if tree_response.status_code == 200:
                    tree_data = tree_response.json()
                    tree_items = tree_data.get("tree", [])
                    file_tree = self.format_tree(tree_items)

                # Find and fetch README
                readme_content = await self.fetch_readme(
                    client, headers, owner, repo, tree_items
                )

                # Build context using prompt template
                context = self.agent.read_prompt(
                    "agent.extras.repo_mention.md",
                    owner=owner,
                    repo=repo,
                    full_name=repo_data.get("full_name", f"{owner}/{repo}"),
                    description=repo_data.get("description") or "",
                    language=repo_data.get("language") or "Not specified",
                    stars=repo_data.get("stargazers_count", 0),
                    default_branch=default_branch,
                    file_tree=file_tree,
                    readme_content=readme_content,
                )

                return context

        except Exception:
            return None

    async def fetch_readme(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        owner: str,
        repo: str,
        tree_items: list,
    ) -> str:
        """Find a README file in the tree and fetch its raw content."""
        readme_names = {"readme.md", "readme", "readme.rst", "readme.txt"}

        readme_path = ""
        for item in tree_items:
            path = item.get("path", "")
            if path.lower() in readme_names and item.get("type") == "blob":
                readme_path = path
                break

        if not readme_path:
            return ""

        try:
            raw_headers = {
                **headers,
                "Accept": "application/vnd.github.raw+json",
            }
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_path}",
                headers=raw_headers,
            )
            if resp.status_code != 200:
                return ""

            content = resp.text
            max_len = 4000
            if len(content) > max_len:
                content = content[:max_len] + "\n\n... (truncated)"
            return content
        except Exception:
            return ""

    def format_tree(self, items: list, max_items: int = 100) -> str:
        """Format tree items into readable directory structure."""
        if not items:
            return "No files found"

        # Filter to max depth of 3 levels
        filtered = []
        for item in items:
            path = item.get("path", "")
            depth = path.count("/")
            if depth <= 2:  # 0, 1, 2 = 3 levels
                filtered.append(item)

        # Sort: directories first, then files, alphabetically
        def sort_key(item):
            is_tree = item.get("type") == "tree"
            path = item.get("path", "")
            return (not is_tree, path.lower())

        filtered.sort(key=sort_key)

        # Format output with truncation
        lines = []
        truncated = len(filtered) > max_items
        display_items = filtered[:max_items]

        for item in display_items:
            path = item.get("path", "")
            item_type = item.get("type", "blob")
            prefix = "/" if item_type == "tree" else ""
            lines.append(f"{prefix}{path}")

        if truncated:
            remaining = len(filtered) - max_items
            lines.append(f"... and {remaining} more items")

        return "\n".join(lines)
