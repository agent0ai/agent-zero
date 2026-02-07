from python.helpers.api import ApiHandler, Request, Response
from python.helpers import runtime, files
import os
import fnmatch


class FileSearch(ApiHandler):
    """Search workspace files by filename pattern for @ file mentions."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        query = input.get("query", "").strip()
        if not query:
            return {"results": []}

        results = await runtime.call_development_function(search_files, query)
        return {"results": results}


async def search_files(query: str, max_results: int = 50) -> list[dict]:
    """Search the agent workspace for files matching the query."""
    work_dir = "/a0"
    results = []
    query_lower = query.lower()
    pattern = f"*{query_lower}*"

    for root, dirs, filenames in os.walk(work_dir):
        # Skip hidden directories and common noise
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".")
            and d not in ("node_modules", "__pycache__", ".git", "venv", ".venv")
        ]

        for filename in filenames:
            if fnmatch.fnmatch(filename.lower(), pattern):
                full_path = os.path.join(root, filename)
                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    size = 0

                results.append({
                    "path": full_path,
                    "name": filename,
                    "source": "workspace",
                    "size": size,
                })

                if len(results) >= max_results:
                    return results

    return results
