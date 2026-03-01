import json
from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers import files
from python.helpers.print_style import PrintStyle

FLOWS_DIR = "usr/flows"


class FlowList(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        try:
            if not files.exists(FLOWS_DIR):
                return {"ok": True, "flows": []}

            flow_files = files.list_files(FLOWS_DIR, "*.json")
            flows = []

            for fname in flow_files:
                try:
                    content = files.read_file(f"{FLOWS_DIR}/{fname}")
                    data = json.loads(content)
                    flows.append({
                        "name": data.get("name", fname.replace(".json", "")),
                        "description": data.get("description", ""),
                        "filename": fname,
                    })
                except Exception:
                    continue

            return {"ok": True, "flows": flows}

        except Exception as e:
            PrintStyle.error(f"Failed to list flows: {e}")
            return {"ok": False, "error": str(e), "flows": []}
