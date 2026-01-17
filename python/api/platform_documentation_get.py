import os

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class platform_documentation_get(ApiHandler):
    """API handler to retrieve the platform documentation."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            doc_path = files.get_abs_path("docs/PLATFORM_DOCUMENTATION.md")
            if not os.path.exists(doc_path):
                return {"success": False, "error": "Documentation file not found."}

            with open(doc_path, encoding='utf-8') as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "last_updated": os.path.getmtime(doc_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
