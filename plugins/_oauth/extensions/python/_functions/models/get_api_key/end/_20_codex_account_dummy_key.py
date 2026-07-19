from __future__ import annotations

from helpers.extension import Extension


DUMMY_API_KEY = "oauth"
PROVIDERS = {"codex_oauth"}


class CodexAccountDummyKey(Extension):
    def execute(self, data: dict | None = None, **kwargs):
        if not isinstance(data, dict):
            return

        args = data.get("args")
        call_kwargs = data.get("kwargs")
        service = ""
        if isinstance(args, tuple) and args:
            service = str(args[0] or "")
        elif isinstance(call_kwargs, dict):
            service = str(call_kwargs.get("service") or "")

        if service.lower() not in PROVIDERS:
            return

        result = str(data.get("result") or "").strip()
        if not result or result == "None":
            data["result"] = DUMMY_API_KEY
