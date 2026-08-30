"""
Repair near-miss tool requests before Agent Zero's strict extractor sees them.

Why this exists
---------------
Since commit 6b7302f6 (2026-07-23, "fix(tools): harden malformed text tool
handling"), `helpers/extract_tools.extract_tool_request()` requires the ENTIRE
stripped assistant message to be exactly one JSON root:

    root = extract_json_root_string(content)
    if root != content:
        return None            # -> agent.py logs "no valid tool request found"

Before that commit `process_tools()` used `json_parse_dirty()`, which happily
found a tool-shaped JSON object anywhere inside the message. So any model that
emits a leading "Sure:", a trailing "Done.", a ```json fence, a leaked
<think> block, a harmony <|channel|> preamble, or a BOM now trips the misformat
warning even though its JSON is perfectly well-formed.

This extension runs at the `start` point of `Agent.process_tools`, normalizes
the message, and rewrites it to canonical JSON so the strict check passes.
It changes nothing when the message is already clean.

Install to (create dirs as needed):
    usr/extensions/python/_functions/agent/Agent/process_tools/start/_10_repair_tool_request.py
"""

from __future__ import annotations

__version__ = "2026.08.18-g"

import json
import re
from typing import Any

from helpers import extract_tools
from helpers.extension import Extension

# This extension needs a post-6b7302f6 extract_tools API. On older Agent Zero
# builds these helpers do not exist; degrade to a no-op instead of raising
# AttributeError inside the agent loop.
_REQUIRED = ("extract_tool_request", "json_parse_dirty",
             "extract_json_root_strings", "normalize_tool_request")
COMPATIBLE = all(hasattr(extract_tools, fn) for fn in _REQUIRED)
MISSING = [fn for fn in _REQUIRED if not hasattr(extract_tools, fn)]

# Zero-width / BOM characters that survive str.strip() and break `root == content`
_INVISIBLES = "\ufeff\u200b\u200c\u200d\u2060"

# Reasoning wrappers that some providers leak into the content channel
_REASONING_BLOCKS = [
    re.compile(r"<think\b[^>]*>.*?</think\s*>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<thinking\b[^>]*>.*?</thinking\s*>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<reasoning\b[^>]*>.*?</reasoning\s*>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<scratchpad\b[^>]*>.*?</scratchpad\s*>", re.DOTALL | re.IGNORECASE),
    re.compile(r"◁think▷.*?◁/think▷", re.DOTALL),
    # gpt-oss / harmony channel framing
    re.compile(r"<\|channel\|>.*?<\|message\|>", re.DOTALL),
    re.compile(r"<\|(?:start|end|return|constrain)\|>"),
    # Unclosed reasoning block running up to the JSON payload
    re.compile(r"<(?:think|thinking|reasoning)\b[^>]*>(?![\s\S]*</)[\s\S]*?(?=\{)", re.IGNORECASE),
]

# Native tool-call markup some models emit instead of the JSON envelope.
_CALL_TAGS = r"invoke|function_call|function|tool_call|tool_use"
_ARG_TAGS = r"parameter|argument|property"

# <invoke name="x">, <function name="x" foo="bar">, any attribute order
_XML_INVOKE = re.compile(
    r"<(?:antml:)?(?:" + _CALL_TAGS + r")\b[^>]*?\bname\s*=\s*[\"']([^\"']+)[\"'][^>]*>"
    r"(.*?)</(?:antml:)?(?:" + _CALL_TAGS + r")\s*>",
    re.DOTALL | re.IGNORECASE,
)
# <function=tool_name> ... </function>  (functionary / llama style)
_XML_INVOKE_EQ = re.compile(
    r"<(?:antml:)?(?:" + _CALL_TAGS + r")\s*=\s*[\"']?([\w.\-]+)[\"']?\s*>"
    r"(.*?)</(?:antml:)?(?:" + _CALL_TAGS + r")\s*>",
    re.DOTALL | re.IGNORECASE,
)
_XML_PARAM = re.compile(
    r"<(?:antml:)?(?:" + _ARG_TAGS + r")\b[^>]*?\bname\s*=\s*[\"']([^\"']+)[\"'][^>]*>"
    r"(.*?)</(?:antml:)?(?:" + _ARG_TAGS + r")\s*>",
    re.DOTALL | re.IGNORECASE,
)
_XML_TOOLCALL = re.compile(
    r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL | re.IGNORECASE
)

_FENCE = re.compile(r"```[ \t]*(?:json|jsonc|json5)?[ \t]*\r?\n(.*?)```", re.DOTALL | re.IGNORECASE)


# HTML line breaks appearing inside the JSON envelope. Seen in the wild as
# '{<br>    "thoughts": [<br>...' - the envelope is complete and correct but
# newlines arrived as <br>, so every parser fails at column 2.
_HTML_BR = re.compile(r"<\s*br\s*/?\s*>", re.IGNORECASE)


def _unbreak_html(text: str) -> str:
    """Convert <br> back to real newlines when they appear inside a JSON body."""
    if not _HTML_BR.search(text):
        return text
    stripped = text.strip()
    # Only touch things that look like a JSON envelope, never prose.
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return text
    return _HTML_BR.sub("\n", text)


def _strip_wrappers(text: str) -> str:
    for ch in _INVISIBLES:
        text = text.replace(ch, "")
    for pattern in _REASONING_BLOCKS:
        text = pattern.sub("", text)
    text = _unbreak_html(text)
    return text.strip()


def _coerce_args(request: dict[str, Any]) -> dict[str, Any]:
    """Normalize alias shapes and stringified args into the canonical envelope."""
    # {"name": ..., "arguments": {...}}  (Hermes / OpenAI tool_call shape)
    if not request.get("tool_name") and not request.get("tool"):
        if isinstance(request.get("name"), str):
            request["tool_name"] = request["name"]
        fn = request.get("function")
        if isinstance(fn, dict) and isinstance(fn.get("name"), str):
            request["tool_name"] = fn["name"]
            if fn.get("arguments") is not None:
                request.setdefault("arguments", fn["arguments"])
    if "tool_args" not in request and "arguments" in request:
        request["tool_args"] = request["arguments"]

    for key in ("tool_args", "args", "parameters", "arguments"):
        value = request.get(key)
        if isinstance(value, str) and value.strip().startswith("{"):
            parsed = extract_tools.json_parse_dirty(value)
            if isinstance(parsed, dict):
                request[key] = parsed
    return request


def _xml_envelopes(text: str):
    """Convert native XML/function-call markup into A0 tool envelopes."""
    for match in _XML_TOOLCALL.finditer(text):
        parsed = extract_tools.json_parse_dirty(match.group(1))
        if isinstance(parsed, dict):
            yield parsed

    seen_spans = []
    for match in list(_XML_INVOKE.finditer(text)) + list(_XML_INVOKE_EQ.finditer(text)):
        if any(a <= match.start() < b for a, b in seen_spans):
            continue
        seen_spans.append((match.start(), match.end()))
        name = match.group(1).strip()
        args: dict[str, Any] = {}
        for pname, pvalue in _XML_PARAM.findall(match.group(2)):
            value = pvalue.strip()
            # A JSON-looking parameter body should land as structured data
            if value[:1] in "{[":
                parsed = extract_tools.json_parse_dirty(value)
                args[pname.strip()] = parsed if parsed is not None else value
            else:
                args[pname.strip()] = value
        if not name:
            continue
        # The XML wrapper may carry the ENVELOPE fields rather than tool args,
        # e.g. <argument name="tool_name">x</argument>. Prefer that reading.
        if isinstance(args.get("tool_name"), str) and args["tool_name"].strip():
            yield dict(args)
        yield {"thoughts": [], "headline": f"Using {name}", "tool_name": name, "tool_args": args}


_RAW_TOOL_NAME = re.compile(r'"tool_name"\s*:\s*"([^"\\\n]{1,80})"')


def _balanced_object_at(text: str, start: int) -> str | None:
    """Return the balanced {...} beginning at or after `start`, else None."""
    open_at = text.find("{", start)
    if open_at == -1:
        return None
    depth = 0
    quote = None
    esc = False
    for i in range(open_at, len(text)):
        ch = text[i]
        if quote:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                quote = None
            continue
        if ch == '"':
            quote = '"'
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                return text[open_at : i + 1]
    return None  # never closed -> genuinely truncated


def _rebuild_from_raw(text: str):
    """Recover an envelope DirtyJson swallowed into the `thoughts` array.

    Upstream documents this failure (extract_tools.py.dox.md) but only
    re-prompts. Here we read tool_name and tool_args straight off the raw text.
    """
    match = _RAW_TOOL_NAME.search(text)
    if not match:
        return None
    name = match.group(1).strip()
    if not name:
        return None

    idx = text.find('"tool_args"', match.end())
    if idx == -1:
        idx = text.find('"tool_args"')
    if idx == -1:
        return None

    blob = _balanced_object_at(text, idx)
    if blob is None:
        return None  # truncated: refuse rather than fabricate

    args = extract_tools.json_parse_dirty(blob)
    if not isinstance(args, dict):
        try:
            args = json.loads(blob)
        except Exception:
            return None
    if not isinstance(args, dict):
        return None
    return {
        "thoughts": [],
        "headline": f"Using {name}",
        "tool_name": name,
        "tool_args": args,
    }


def _xml_loose_envelope(text: str):
    """<argument name="tool_name">x</argument> with no parseable wrapper tag."""
    params = dict(
        (k.strip(), v.strip()) for k, v in _XML_PARAM.findall(text)
    )
    if isinstance(params.get("tool_name"), str) and params["tool_name"].strip():
        return params
    return None


def _candidate_requests(text: str):
    """Yield every plausible tool-request dict found in the text, best first."""
    # 0. strict parse first - DirtyJson can mangle input that is actually valid
    try:
        strict = json.loads(text)
        if isinstance(strict, dict):
            yield strict
    except Exception:
        pass

    # 1. whole text
    yield extract_tools.json_parse_dirty(text)

    # 2. inside markdown fences
    for fenced in _FENCE.findall(text):
        yield extract_tools.json_parse_dirty(fenced)

    # 3. each complete JSON root embedded in surrounding prose
    for root in extract_tools.extract_json_root_strings(text):
        yield extract_tools.json_parse_dirty(root)

    # 3b. envelope absorbed into `thoughts` by the dirty parser
    rebuilt = _rebuild_from_raw(text)
    if rebuilt is not None:
        yield rebuilt

    # 4. native XML / function-call markup
    yield from _xml_envelopes(text)
    loose = _xml_loose_envelope(text)
    if loose is not None:
        yield loose

    # 5. single-element array wrapper: [ { ...tool... } ]
    stripped = text.lstrip()
    if stripped.startswith("["):
        try:
            arr = json.loads(stripped)
        except Exception:
            arr = None
        if isinstance(arr, list) and len(arr) == 1 and isinstance(arr[0], dict):
            yield arr[0]


def repair(message: str) -> str | None:
    """Return canonical JSON for a repairable message, else None."""
    if not COMPATIBLE:
        return None
    if not isinstance(message, str) or not message.strip():
        return None

    # Already accepted by the strict extractor - do not touch it.
    if extract_tools.extract_tool_request(message) is not None:
        return None

    text = _strip_wrappers(message)
    if not text:
        return None

    for candidate in _candidate_requests(text):
        if not isinstance(candidate, dict):
            continue
        candidate = _coerce_args(dict(candidate))
        try:
            extract_tools.normalize_tool_request(candidate)
        except ValueError:
            continue
        canonical = json.dumps(candidate, ensure_ascii=False)
        # Guard: only hand back something the strict extractor will accept.
        if extract_tools.extract_tool_request(canonical) is not None:
            return canonical
    return None


class RepairToolRequest(Extension):
    _warned = False

    def execute(self, data: dict[str, Any] | None = None, **kwargs):
        if not COMPATIBLE:
            if not RepairToolRequest._warned:
                RepairToolRequest._warned = True
                print(f"[repair_tool_request] incompatible Agent Zero build; "
                      f"missing {MISSING}. Extension disabled.")
            return
        if not isinstance(data, dict):
            return

        call_kwargs = data.get("kwargs")
        call_args = data.get("args")

        message = None
        source = None
        if isinstance(call_kwargs, dict) and isinstance(call_kwargs.get("msg"), str):
            message, source = call_kwargs["msg"], "kwargs"
        elif isinstance(call_args, tuple) and len(call_args) > 1 and isinstance(call_args[1], str):
            message, source = call_args[1], "args"

        if message is None:
            return

        try:
            repaired = repair(message)
        except Exception as exc:  # never break process_tools
            print(f"[repair_tool_request] repair failed, passing through: {exc!r}")
            return
        if repaired is None:
            return

        if source == "kwargs":
            new_kwargs = dict(call_kwargs)  # type: ignore[arg-type]
            new_kwargs["msg"] = repaired
            data["kwargs"] = new_kwargs
        else:
            args = list(call_args)  # type: ignore[arg-type]
            args[1] = repaired
            data["args"] = tuple(args)
