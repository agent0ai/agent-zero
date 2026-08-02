
import json

from .dirty_json import DirtyJson
import regex, re
from helpers.modules import load_classes_from_file, load_classes_from_folder # keep here for backwards compatibility
from typing import Any

def json_parse_dirty(json: str) -> dict[str, Any] | None:
    if not json or not isinstance(json, str):
        return None

    first_data: dict[str, Any] | None = None
    for ext_json in extract_json_root_strings(json.strip()):
        data = _parse_json_root_object(ext_json)
        if data is None:
            continue
        if first_data is None:
            first_data = data
        if _is_tool_request(data):
            return data
    return first_data


def extract_tool_request(content: str) -> dict[str, Any] | None:
    if not content or not isinstance(content, str):
        return None

    content = content.strip()
    root = extract_json_root_string(content)
    if root != content:
        return None

    request = _parse_json_root_object(root)
    return request if request is not None and _is_tool_request(request) else None


def recover_embedded_tool_request(content: str) -> dict[str, Any] | None:
    """Recover exactly one valid tool request embedded in surrounding prose.

    Strict extraction (extract_tool_request) stays unchanged; this is a
    narrowly scoped repair for models (e.g. DeepSeek V4 Flash with thinking
    enabled) that occasionally wrap a single valid JSON tool envelope in
    planning prose. Returns None when zero or multiple *distinct* tool
    requests are found, so arbitrary prose is never treated as a tool call.

    Envelopes appearing inside quoted spans, inline code, or fenced code
    blocks are examples being discussed, not requests being issued, and are
    masked before scanning. Candidates must parse as strict JSON, so lenient
    dirty-JSON forms (single-quoted keys, etc.) are not executable either.
    """
    if not content or not isinstance(content, str):
        return None

    content = content.strip()
    if extract_tool_request(content) is not None:
        return None  # strict path handles clean responses; recovery is failure-only

    masked = _mask_non_executable_regions(content)
    distinct: dict[str, dict[str, Any]] = {}
    root_for_request = ""
    for root in extract_json_root_strings(masked):
        data = _parse_json_root_object_strict(root)
        if data is None or not _is_tool_request(data):
            continue
        distinct.setdefault(json.dumps(data, sort_keys=True, default=str), data)
        if len(distinct) > 1:
            return None
        root_for_request = root
    request = next(iter(distinct.values()), None)
    if request is None:
        return None
    if str(request.get("tool_name") or "") == "response" and _has_prose_around(
        masked, root_for_request
    ):
        # A "response" envelope buried in deliberating prose is the model
        # thinking out loud about how it *could* reply, not a completed task.
        # Refuse recovery so the message takes the standard misformat path
        # instead of ending the task. Operational tools keep being recovered:
        # executing a valid operational envelope is the protocol's intent.
        return None
    return request


_RESPONSE_PROSE_HEDGE_RE = re.compile(
    r"\b(could|might|maybe|option|alternatively|but)\b", re.IGNORECASE
)


def _has_prose_around(masked_content: str, root: str) -> bool:
    """Heuristic: True when substantial prose surrounds the extracted root.

    Deliberately simple and deterministic: prose is substantial when the
    non-whitespace text outside the JSON root exceeds 40 characters, or when
    it contains hedging language ("could", "but", ...) that marks the
    envelope as a possibility under discussion rather than the final answer.
    Quoted/fenced spans are already blanked by _mask_non_executable_regions,
    so examples under discussion do not count as prose.
    """
    prose = masked_content.replace(root, " ", 1)
    if len("".join(prose.split())) > 40:
        return True
    return bool(_RESPONSE_PROSE_HEDGE_RE.search(prose))


def _mask_non_executable_regions(content: str) -> str:
    """Blank out fenced code blocks, inline code and top-level quoted spans.

    Quoted/fenced regions in prose contain examples under discussion, not a
    tool request the model is issuing. Masking them (to spaces, preserving
    newlines and offsets) prevents the root scanner from starting a JSON
    object inside them. Quotes inside an actual JSON object (depth > 0) are
    left untouched, so a legitimate bare envelope survives masking.
    """
    chars = list(content)

    for match in re.finditer(r"```.*?```", content, flags=re.DOTALL):
        for index in range(match.start(), match.end()):
            if chars[index] != "\n":
                chars[index] = " "

    depth = 0
    quote: str | None = None
    escaped = False
    for index, char in enumerate(chars):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            if char != "\n":
                chars[index] = " "
            continue

        if char in "{[":
            depth += 1
        elif char in "}]":
            depth = max(0, depth - 1)
        elif depth == 0 and char in ('"', "`"):
            quote = char
            chars[index] = " "

    return "".join(chars)


def _parse_json_root_object_strict(root: str) -> dict[str, Any] | None:
    try:
        data = json.loads(root)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def explain_tool_request_failure(content: str, finish_reason: str = "") -> str:
    """Sanitized classification of why no tool request could be extracted.

    Never includes response content; only a reason and the output length.
    """
    prefix = ""
    if finish_reason == "length":
        prefix = "provider truncated the response (finish_reason=length); "

    if not isinstance(content, str) or not content.strip():
        return f"{prefix}empty response from the model"

    stripped = content.strip()
    length = len(stripped)
    if "{" not in stripped:
        return f"{prefix}plain prose with no JSON tool object ({length} chars)"

    roots = extract_json_root_strings(stripped)
    if roots:
        # A complete (non-tool) root followed by an unterminated fragment
        # (odd quote count, or a new "{") is trailing truncation, not a
        # clean-but-invalid envelope.
        tail = stripped.split(roots[-1], 1)[1].lstrip(" \t\r\n,")
        if tail and (tail.startswith("{") or tail.count('"') % 2 == 1):
            return (
                f"{prefix}truncated or unterminated JSON tool request "
                f"({length} chars)"
            )
        return (
            f"{prefix}JSON object without a valid tool_name/tool_args envelope "
            f"({length} chars)"
        )

    return f"{prefix}truncated or unterminated JSON tool request ({length} chars)"


def is_misformatted_tool_request(content: str) -> bool:
    if not content or not isinstance(content, str):
        return False

    content = content.strip()
    roots = extract_json_root_strings(content)
    if (
        len(roots) > 1
        and content.startswith("{")
        and content.endswith("}")
        and any(extract_tool_request(root) is not None for root in roots)
    ):
        return True

    for fenced_content in re.findall(
        r"```(?:json)?\s*(.*?)```", content, flags=re.IGNORECASE | re.DOTALL
    ):
        request = json_parse_dirty(fenced_content)
        if isinstance(request, dict) and _is_tool_request(request):
            return True

    if (
        not content.endswith("}")
        or re.match(r'^\{\s*"thoughts"\s*:', content) is None
    ):
        return False

    request = json_parse_dirty(content)
    thoughts = request.get("thoughts") if isinstance(request, dict) else None
    thoughts_text = (
        "\n".join(thought for thought in thoughts if isinstance(thought, str))
        if isinstance(thoughts, list)
        else ""
    )
    return (
        isinstance(thoughts, list)
        and all(
            f'{field}\":' in thoughts_text
            for field in ("headline", "tool_name", "tool_args")
        )
    )

def _json_scan_final_depth(content: str) -> int:
    """Return the unclosed-brace depth after scanning JSON-ish text.

    Tracks quote/escape state so braces inside strings do not count. Shared
    by _json_root_object_balanced and is_truncated_tool_request so the two
    scans cannot drift apart. Depth > 0 means the text is unterminated.
    """
    depth = 0
    quote = None
    escaped = False
    for char in content:
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if depth and char in ('"', "'", "`"):
            quote = char
        elif char == "{":
            depth += 1
        elif depth and char == "[":
            depth += 1
        elif depth and char in ("}", "]"):
            depth -= 1
    return depth


def _json_root_object_balanced(content: str) -> bool:
    return _json_scan_final_depth(content) == 0


def is_truncated_tool_request(content: str) -> bool:
    """Return True when content is an unterminated JSON tool envelope.

    Used by the harness to give a targeted retry prompt instead of a generic
    misformat warning when providers cut a streaming/completion response
    mid-object.
    """
    if not content or not isinstance(content, str):
        return False
    content = content.strip()
    if not content.startswith("{"):
        return False
    if content.endswith("}") and _json_root_object_balanced(content):
        return False

    if _json_scan_final_depth(content) <= 0:
        return False
    # Structural gate: the payload must open like a JSON tool envelope
    # ({"thoughts"/"headline"/"tool_name"/"tool_args": ...) or a Responses
    # function_call-style payload ({"type":"function", ...). A prose sentence
    # that merely mentions "tool"/"actions"/"function" after a stray "{" is
    # not a truncated request. "type" is included because in responses mode a
    # truncated function-call payload must take the repair-prompt path instead
    # of being shown to the user as a plain-text reply.
    return (
        re.match(r'^\{\s*"(thoughts|headline|tool_name|tool_args|type)"', content)
        is not None
    )

def normalize_tool_request(tool_request: Any) -> tuple[str, dict]:
    if not isinstance(tool_request, dict):
        raise ValueError("Tool request must be a dictionary")
    if (
        not tool_request.get("tool_name")
        and not tool_request.get("tool")
        and "actions" in tool_request
    ):
        actions = tool_request["actions"]
        # Text tool calls allow one request per turn; do not silently discard extras.
        if (
            not isinstance(actions, list)
            or len(actions) != 1
            or not isinstance(actions[0], dict)
        ):
            raise ValueError(
                "Tool request actions wrapper must contain exactly one dictionary"
            )
        tool_request = actions[0]

    tool_name = tool_request.get("tool_name")
    if not tool_name or not isinstance(tool_name, str):
        tool_name = tool_request.get("tool")
    if (
        (not tool_name or not isinstance(tool_name, str))
        and tool_request.get("type") == "function"
    ):
        tool_name = tool_request.get("name")
    if not tool_name or not isinstance(tool_name, str):
        raise ValueError("Tool request must have a tool_name (type string) field")
    tool_args = tool_request.get("tool_args")
    if not isinstance(tool_args, dict):
        tool_args = tool_request.get("args")
    if not isinstance(tool_args, dict) and tool_request.get("type") == "function":
        tool_args = tool_request.get("parameters")
    if not isinstance(tool_args, dict):
        raise ValueError("Tool request must have a tool_args (type dictionary) field")
    tool_args = dict(tool_args)
    if ":" in tool_name:
        tool_name, action = tool_name.split(":", 1)
        if not tool_name or not action:
            raise ValueError("tool_name method suffix must include tool and action")
        tool_args.setdefault("action", action)
    method = tool_args.get("method")
    if "action" not in tool_args and isinstance(method, str) and method:
        tool_args["action"] = method
    return tool_name, tool_args


def extract_json_root_string(content: str) -> str | None:
    first_root: str | None = None
    for root in extract_json_root_strings(content):
        if first_root is None:
            first_root = root
        data = _parse_json_root_object(root)
        if data is not None and _is_tool_request(data):
            return root
    return first_root


def extract_json_root_strings(content: str) -> list[str]:
    if not content or not isinstance(content, str):
        return []

    if content.lstrip().startswith("["):
        # Blind spot, by design: content starting with "[" is treated as a
        # JSON array and never scanned for object roots, so embedded-envelope
        # recovery can never fire for it.
        return []

    roots: list[str] = []
    for start in _json_root_object_starts(content):
        parser = DirtyJson()
        try:
            parser.parse(content[start:])
        except Exception:
            continue

        if not parser.completed:
            continue

        roots.append(content[start : start + parser.index])
    return roots


def _json_root_object_starts(content: str) -> list[int]:
    starts: list[int] = []
    depth = 0
    quote: str | None = None
    escaped = False

    for index, char in enumerate(content):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if depth and char in ['"', "'", "`"]:
            quote = char
        elif char == "{":
            if depth == 0:
                starts.append(index)
            depth += 1
        elif depth and char == "[":
            depth += 1
        elif depth and char in ["}", "]"]:
            depth -= 1

    return starts


def _parse_json_root_object(root: str) -> dict[str, Any] | None:
    try:
        data = DirtyJson.parse_string(root)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _is_tool_request(data: dict[str, Any]) -> bool:
    try:
        normalize_tool_request(data)
    except ValueError:
        return False
    return True


def extract_json_object_string(content):
    start = content.find("{")
    if start == -1:
        return ""

    # Find the first '{'
    end = content.rfind("}")
    if end == -1:
        # If there's no closing '}', return from start to the end
        return content[start:]
    else:
        # If there's a closing '}', return the substring from start to end
        return content[start : end + 1]


def extract_json_string(content):
    # Regular expression pattern to match a JSON object
    pattern = r'\{(?:[^{}]|(?R))*\}|\[(?:[^\[\]]|(?R))*\]|"(?:\\.|[^"\\])*"|true|false|null|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'

    # Search for the pattern in the content
    match = regex.search(pattern, content)

    if match:
        # Return the matched JSON string
        return match.group(0)
    else:
        return ""


def fix_json_string(json_string):
    # Function to replace unescaped line breaks within JSON string values
    def replace_unescaped_newlines(match):
        return match.group(0).replace("\n", "\\n")

    # Use regex to find string values and apply the replacement function
    fixed_string = re.sub(
        r'(?<=: ")(.*?)(?=")', replace_unescaped_newlines, json_string, flags=re.DOTALL
    )
    return fixed_string
