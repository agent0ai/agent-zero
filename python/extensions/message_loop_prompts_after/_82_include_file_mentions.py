from python.helpers.extension import Extension
from agent import LoopData
import httpx
import os

MAX_FILE_CHARS = 10000
LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".jsx": "jsx",
    ".tsx": "tsx", ".html": "html", ".css": "css", ".json": "json",
    ".md": "markdown", ".yaml": "yaml", ".yml": "yaml", ".sh": "bash",
    ".sql": "sql", ".rs": "rust", ".go": "go", ".java": "java",
    ".rb": "ruby", ".php": "php", ".c": "c", ".cpp": "cpp", ".h": "c",
    ".xml": "xml", ".toml": "toml", ".ini": "ini", ".cfg": "ini",
}


class IncludeFileMentions(Extension):
    """Inject @mentioned file contents into agent prompts."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        mentions = self.agent.data.get("mentions", [])
        file_mentions = [m for m in mentions if m.get("type") == "file"]
        if not file_mentions:
            return

        for mention in file_mentions:
            source = mention.get("source", "")
            content = None

            if source == "workspace":
                content = self._read_workspace_file(mention)
            elif source == "github":
                content = await self._fetch_github_file(mention)
            elif source == "upload":
                content = mention.get("content", "")

            if content is not None:
                content = self._truncate(content)
                path = mention.get("path", "unknown")
                lang = self._detect_language(path)

                context = self.agent.read_prompt(
                    "agent.extras.file_mention.md",
                    path=path,
                    source=source,
                    language=lang,
                    content=content,
                )

                if context:
                    key = f"file_mention_{path.replace('/', '_')}"
                    loop_data.extras_temporary[key] = context

    def _read_workspace_file(self, mention: dict) -> str | None:
        path = mention.get("path", "")
        if not path:
            return None
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return None

    async def _fetch_github_file(self, mention: dict) -> str | None:
        from python.api.github_callback import get_github_auth

        auth_data = get_github_auth()
        if not auth_data:
            return None

        access_token = auth_data.get("access_token")
        if not access_token:
            return None

        repo = mention.get("repo", "")
        path = mention.get("path", "")
        if not repo or not path:
            return None

        # repo is "owner/repo-name"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.raw+json",
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://api.github.com/repos/{repo}/contents/{path}",
                    headers=headers,
                )
                if resp.status_code != 200:
                    return None
                return resp.text
        except Exception:
            return None

    def _truncate(self, content: str) -> str:
        if len(content) > MAX_FILE_CHARS:
            return content[:MAX_FILE_CHARS] + "\n\n... (truncated)"
        return content

    def _detect_language(self, path: str) -> str:
        _, ext = os.path.splitext(path.lower())
        return LANGUAGE_MAP.get(ext, "")
