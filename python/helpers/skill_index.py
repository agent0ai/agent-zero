"""JumboHub skill index client: search, fetch, publish, and cache management.

Uses urllib.request from the standard library with optional httpx acceleration.
"""

from __future__ import annotations

import json
import ssl
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from python.helpers.skill_packager import SkillPackager

# ---------------------------------------------------------------------------
# Optional httpx for better async HTTP (graceful fallback to urllib)
# ---------------------------------------------------------------------------
try:
    import httpx

    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


def _http_get(url: str, headers: dict[str, str] | None = None) -> bytes:
    """Synchronous HTTP GET using httpx (if available) or urllib."""
    if _HAS_HTTPX:
        with httpx.Client(follow_redirects=True, timeout=30) as client:
            resp = client.get(url, headers=headers or {})
            resp.raise_for_status()
            return resp.content
    else:
        req = Request(url, headers=headers or {})
        ctx = ssl.create_default_context()
        with urlopen(req, context=ctx, timeout=30) as resp:  # nosec B310
            return resp.read()


def _http_post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Synchronous HTTP POST (JSON body) using httpx or urllib."""
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    data = json.dumps(payload).encode()

    if _HAS_HTTPX:
        with httpx.Client(follow_redirects=True, timeout=30) as client:
            resp = client.post(url, content=data, headers=hdrs)
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]
    else:
        req = Request(url, data=data, headers=hdrs, method="POST")
        ctx = ssl.create_default_context()
        with urlopen(req, context=ctx, timeout=30) as resp:  # nosec B310
            return json.loads(resp.read())  # type: ignore[no-any-return]


class SkillIndex:
    """Client for the JumboHub skill index (GitHub-hosted JSON catalog)."""

    INDEX_URL = "https://raw.githubusercontent.com/agent-jumbo/jumbohub/main/index.json"
    PUBLISH_API = "https://api.github.com/repos/agent-jumbo/jumbohub/releases"

    def __init__(
        self,
        index_url: str | None = None,
        cache_dir: str = "data/skill_cache",
    ) -> None:
        self.index_url = index_url or self.INDEX_URL
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index: list[dict[str, Any]] = []
        self._index_file = self.cache_dir / "index.json"
        self._load_cached_index()

    # -- public API -----------------------------------------------------------

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Search the index for skills matching *query* (case-insensitive)."""
        if not self._index:
            await self.refresh_index()

        q = query.lower()
        results: list[dict[str, Any]] = []
        for entry in self._index:
            haystack = " ".join(
                [
                    entry.get("name", ""),
                    entry.get("description", ""),
                    " ".join(entry.get("categories", [])),
                    " ".join(entry.get("capabilities", [])),
                    entry.get("author", ""),
                ]
            ).lower()
            if q in haystack:
                results.append(entry)
        return results

    async def fetch(self, name: str, version: str | None = None) -> Path:
        """Download a skill package to cache and return the local path.

        Verifies SHA256 integrity when the index entry contains a hash.
        """
        if not self._index:
            await self.refresh_index()

        entry = self._find_entry(name, version)
        if entry is None:
            raise LookupError(f"Skill '{name}' not found in the index")

        download_url = entry.get("download_url", "")
        if not download_url:
            raise ValueError(f"No download URL for skill '{name}'")

        pkg_version = entry.get("version", "latest")
        pkg_filename = f"{name}-{pkg_version}.tar.gz"
        pkg_path = self.cache_dir / pkg_filename

        # Download if not already cached.
        if not pkg_path.is_file():
            data = _http_get(download_url)
            pkg_path.write_bytes(data)

        # Verify SHA256 if available.
        expected_sha = entry.get("sha256")
        if expected_sha:
            packager = SkillPackager()
            if not packager.verify(pkg_path, expected_sha):
                pkg_path.unlink(missing_ok=True)
                raise ValueError(f"SHA256 mismatch for '{name}': expected {expected_sha}")

        return pkg_path

    async def publish(self, skill_path: Path, token: str) -> dict[str, Any]:
        """Publish a skill to JumboHub by creating a GitHub release.

        *skill_path* should point to the skill directory (containing SKILL.md).
        *token* is a GitHub personal-access token with ``repo`` scope.
        """
        skill_path = Path(skill_path).resolve()
        packager = SkillPackager()
        pkg_path = packager.package(skill_path)
        sha256 = packager.get_sha256(pkg_path)

        skill_name = skill_path.name
        tag = f"{skill_name}-v1"

        payload: dict[str, Any] = {
            "tag_name": tag,
            "name": f"{skill_name} release",
            "body": f"SHA256: {sha256}",
            "draft": False,
            "prerelease": False,
        }

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }

        result = _http_post_json(self.PUBLISH_API, payload, headers=headers)
        result["sha256"] = sha256
        result["package_path"] = str(pkg_path)
        return result

    async def refresh_index(self) -> None:
        """Re-download the index catalog from the remote URL."""
        try:
            data = _http_get(self.index_url)
            self._index_file.write_bytes(data)
            parsed = json.loads(data)
            self._index = parsed if isinstance(parsed, list) else parsed.get("skills", [])
        except (URLError, OSError, json.JSONDecodeError) as exc:
            # Fall back to cached data if available.
            if self._index:
                return
            raise ConnectionError(f"Failed to fetch index from {self.index_url}: {exc}") from exc

    def get_cached(self) -> list[dict[str, Any]]:
        """Return locally cached index entries."""
        return list(self._index)

    # -- internal helpers -----------------------------------------------------

    def _load_cached_index(self) -> None:
        """Load the index from the local cache file if it exists."""
        if self._index_file.is_file():
            try:
                raw = json.loads(self._index_file.read_text(encoding="utf-8"))
                self._index = raw if isinstance(raw, list) else raw.get("skills", [])
            except (json.JSONDecodeError, OSError):
                self._index = []

    def _find_entry(self, name: str, version: str | None = None) -> dict[str, Any] | None:
        """Locate an index entry by name and optional version."""
        for entry in self._index:
            if entry.get("name") == name:
                if version is None or entry.get("version") == version:
                    return entry
        return None
