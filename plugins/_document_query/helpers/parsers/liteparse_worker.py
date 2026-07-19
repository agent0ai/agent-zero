"""Subprocess entry point for isolating LiteParse native runtime crashes."""

from __future__ import annotations

import json
import sys


def main() -> int:
    payload = json.load(sys.stdin)
    file_path = payload["file_path"]
    kwargs = payload.get("kwargs") or {}

    from liteparse import LiteParse

    parser = LiteParse(**kwargs)
    result = parser.parse(file_path)
    text = getattr(result, "text", "") or ""
    json.dump({"text": text}, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
