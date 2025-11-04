from typing import Any
from browser_use.llm import ChatGoogle
from python.helpers import dirty_json


# ------------------------------------------------------------------------------
# Gemini Helper for Output Conformance
# ------------------------------------------------------------------------------
# This function sanitizes and conforms the JSON output from Gemini to match
# the specific schema expectations of the browser-use library. It handles
# markdown fences, aliases actions (like 'complete_task' to 'done'), and
# intelligently constructs a valid 'data' object for the final action.

def gemini_clean_and_conform(text: str):
    obj = None
    try:
        # dirty_json parser is robust enough to handle markdown fences
        obj = dirty_json.parse(text)
    except Exception:
        return None  # return None if parsing fails

    if not isinstance(obj, dict):
        return None

    # Conform actions to browser-use expectations
    if isinstance(obj.get("action"), list):
        normalized_actions = []
        for item in obj["action"]:
            if not isinstance(item, dict):
                continue  # Skip non-dict items

            action_key, action_value = next(iter(item.items()), (None, None))
            if not action_key:
                continue

            # Alias 'complete_task' to 'done' to handle inconsistencies
            if action_key == "complete_task":
                action_key = "done"

            # Create a mutable copy of the value
            v = (action_value or {}).copy()

            if action_key in ("scroll_down", "scroll_up", "scroll"):
                is_down = action_key != "scroll_up"
                v.setdefault("down", is_down)
                v.setdefault("num_pages", 1.0)
                normalized_actions.append({"scroll": v})
            elif action_key == "go_to_url":
                v.setdefault("new_tab", False)
                normalized_actions.append({action_key: v})
            elif action_key == "done":
                # If `data` is missing, construct it from other keys
                if "data" not in v:
                    # Pop fields from the top-level `done` object
                    response_text = v.pop("response", None)
                    summary_text = v.pop("page_summary", None)
                    title_text = v.pop("title", "Task Completed")

                    final_response = response_text or "Task completed successfully." # browser-use expects string
                    final_summary = summary_text or "No page summary available." # browser-use expects string

                    v["data"] = {
                        "title": title_text,
                        "response": final_response,
                        "page_summary": final_summary,
                    }

                v.setdefault("success", True)
                normalized_actions.append({action_key: v})
            else:
                normalized_actions.append(item)
        obj["action"] = normalized_actions

    return dirty_json.stringify(obj)

# ------------------------------------------------------------------------------
# Monkey-patch for browser-use Gemini schema issue
# ------------------------------------------------------------------------------
# The original _fix_gemini_schema in browser_use.llm.google.chat.ChatGoogle
# removes the 'title' property but fails to remove it from the 'required' list,
# causing a validation error with the Gemini API. This patch corrects that behavior.

def _patched_fix_gemini_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a Pydantic model to a Gemini-compatible schema.

    This function removes unsupported properties like 'additionalProperties' and resolves
    $ref references that Gemini doesn't support.
    """

    # Handle $defs and $ref resolution
    if '$defs' in schema:
        defs = schema.pop('$defs')

        def resolve_refs(obj: Any) -> Any:
            if isinstance(obj, dict):
                if '$ref' in obj:
                    ref = obj.pop('$ref')
                    ref_name = ref.split('/')[-1]
                    if ref_name in defs:
                        # Replace the reference with the actual definition
                        resolved = defs[ref_name].copy()
                        # Merge any additional properties from the reference
                        for key, value in obj.items():
                            if key != '$ref':
                                resolved[key] = value
                        return resolve_refs(resolved)
                    return obj
                else:
                    # Recursively process all dictionary values
                    return {k: resolve_refs(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [resolve_refs(item) for item in obj]
            return obj

        schema = resolve_refs(schema)

    # Remove unsupported properties
    def clean_schema(obj: Any) -> Any:
        if isinstance(obj, dict):
            # Remove unsupported properties
            cleaned = {}
            for key, value in obj.items():
                if key not in ['additionalProperties', 'title', 'default']:
                    cleaned_value = clean_schema(value)
                    # Handle empty object properties - Gemini doesn't allow empty OBJECT types
                    if (
                        key == 'properties'
                        and isinstance(cleaned_value, dict)
                        and len(cleaned_value) == 0
                        and isinstance(obj.get('type', ''), str)
                        and obj.get('type', '').upper() == 'OBJECT'
                    ):
                        # Convert empty object to have at least one property
                        cleaned['properties'] = {'_placeholder': {'type': 'string'}}
                    else:
                        cleaned[key] = cleaned_value

            # If this is an object type with empty properties, add a placeholder
            if (
                isinstance(cleaned.get('type', ''), str)
                and cleaned.get('type', '').upper() == 'OBJECT'
                and 'properties' in cleaned
                and isinstance(cleaned['properties'], dict)
                and len(cleaned['properties']) == 0
            ):
                cleaned['properties'] = {'_placeholder': {'type': 'string'}}

            # PATCH: Also remove 'title' from the required list if it exists
            if 'required' in cleaned and isinstance(cleaned.get('required'), list):
                cleaned['required'] = [p for p in cleaned['required'] if p != 'title']

            return cleaned
        elif isinstance(obj, list):
            return [clean_schema(item) for item in obj]
        return obj

    return clean_schema(schema)

def apply():
    """Applies the monkey-patch to ChatGoogle."""
    ChatGoogle._fix_gemini_schema = _patched_fix_gemini_schema
