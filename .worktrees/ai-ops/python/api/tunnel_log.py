import os
from pathlib import Path

from flask import Response

from python.helpers.api import ApiHandler, Request


class TunnelLog(ApiHandler):
    @classmethod
    def get_methods(cls):
        return ["GET"]

    async def process(self, input: dict, request: Request):
        name = request.args.get("name", "tunnel")
        if name not in {"tunnel", "serveo"}:
            return Response(response="Invalid log name", status=400, mimetype="text/plain")

        path = Path("logs") / f"{name}.log"
        if not path.exists():
            return Response(response="Log not found", status=404, mimetype="text/plain")

        data = path.read_text(encoding="utf-8", errors="ignore")
        response = Response(data, mimetype="text/plain")
        response.headers["Content-Disposition"] = f'attachment; filename="{name}.log"'
        return response
