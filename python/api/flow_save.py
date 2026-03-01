import json
import re
from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers import files
from python.helpers.print_style import PrintStyle

FLOWS_DIR = "usr/flows"


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"


class FlowSave(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        flow = input.get("flow")
        if not flow or not isinstance(flow, dict):
            return {"ok": False, "error": "Missing required field: flow"}

        name = flow.get("name", "Untitled Flow")
        if not name:
            return {"ok": False, "error": "Flow must have a name"}

        # Use provided filename or generate from name
        filename = input.get("filename", "")
        if not filename:
            filename = slugify(name) + ".json"
        filename = files.basename(filename)
        if not filename.endswith(".json"):
            filename += ".json"

        try:
            # Ensure directory exists
            files.make_dirs(f"{FLOWS_DIR}/placeholder")

            # Write flow JSON
            content = json.dumps(flow, indent=2)
            files.write_file(f"{FLOWS_DIR}/{filename}", content)

            return {"ok": True, "filename": filename}

        except Exception as e:
            PrintStyle.error(f"Failed to save flow: {e}")
            return {"ok": False, "error": str(e)}
