from __future__ import annotations

import json
from urllib import request as url_request
from urllib import error as url_error


def _post_json(url: str, payload: dict, headers: dict[str, str] | None = None, method: str = "POST") -> dict:
    data = None if method == "GET" else json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = url_request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with url_request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
    except url_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except url_error.URLError as exc:
        raise RuntimeError(f"Connection error: {exc}") from exc
    return json.loads(body) if body else {}


def ollama_available(base_url: str = "http://localhost:11434") -> bool:
    try:
        _post_json(f"{base_url}/api/tags", payload={}, method="GET")
        return True
    except Exception:
        return False


def suggest_answers_with_ollama(
    *,
    model: str,
    questions_text: str,
    profile_json: str,
    base_url: str = "http://localhost:11434",
) -> str:
    """
    Returns a plain-text set of suggestions.
    Safety intent: do not fabricate user details; answer UNKNOWN if the profile doesn't support it.
    """
    system = (
        "You are a survey helper. Help the user answer honestly and consistently.\n"
        "- Do NOT invent personal facts.\n"
        "- If a question requires information not present in the profile, answer: UNKNOWN.\n"
        "- Keep answers concise.\n"
    )
    prompt = (
        f"{system}\n"
        f"USER_PROFILE_JSON:\n{profile_json}\n\n"
        f"SURVEY_QUESTIONS:\n{questions_text}\n\n"
        "Return suggested answers in a readable bullet list."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }
    resp = _post_json(f"{base_url}/api/chat", payload=payload)
    msg = resp.get("message", {}) if isinstance(resp, dict) else {}
    return str(msg.get("content", "")).strip()

