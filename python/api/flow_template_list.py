import json
from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers import files
from python.helpers.print_style import PrintStyle

TEMPLATES_DIR = "flow_templates"


class FlowTemplateList(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        try:
            if not files.exists(TEMPLATES_DIR):
                return {"ok": True, "templates": []}

            template_files = files.list_files(TEMPLATES_DIR, "*.json")
            templates = []

            for fname in template_files:
                try:
                    content = files.read_file(f"{TEMPLATES_DIR}/{fname}")
                    data = json.loads(content)
                    templates.append({
                        "name": data.get("name", fname.replace(".json", "")),
                        "description": data.get("description", ""),
                        "flow": data,
                    })
                except Exception:
                    continue

            return {"ok": True, "templates": templates}

        except Exception as e:
            PrintStyle.error(f"Failed to list flow templates: {e}")
            return {"ok": False, "error": str(e), "templates": []}
