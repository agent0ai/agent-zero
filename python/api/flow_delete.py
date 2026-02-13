import os
from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers import files
from python.helpers.print_style import PrintStyle

FLOWS_DIR = "usr/flows"


class FlowDelete(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        filename = input.get("filename", "")
        if not filename:
            return {"ok": False, "error": "Missing required field: filename"}

        # Sanitize filename to prevent directory traversal
        filename = files.basename(filename)
        if not filename.endswith(".json"):
            filename += ".json"

        try:
            path = f"{FLOWS_DIR}/{filename}"
            if not files.exists(path):
                return {"ok": False, "error": f"Flow not found: {filename}"}

            abs_path = files.get_abs_path(path)
            os.remove(abs_path)

            return {"ok": True, "message": f"Flow {filename} deleted"}

        except Exception as e:
            PrintStyle.error(f"Failed to delete flow: {e}")
            return {"ok": False, "error": str(e)}
