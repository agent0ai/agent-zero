import os
from pathlib import Path

from python.helpers.api import ApiHandler, Request, Response


class TunnelDebug(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from python.api.tunnel import process as tunnel_process

        status = await tunnel_process({"action": "get"})
        logs = {
            "tunnel": _tail_lines("logs/tunnel.log"),
            "serveo": _tail_lines("logs/serveo.log"),
        }

        return {
            "status": status,
            "logs": logs,
            "webhook_url": os.getenv("TELEGRAM_WEBHOOK_URL", ""),
        }


def _tail_lines(path: str, limit: int = 200) -> str:
    abs_path = Path(path)
    if not abs_path.exists():
        return ""
    try:
        lines = abs_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(lines[-limit:])
    except Exception:
        return ""
