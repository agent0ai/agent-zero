from __future__ import annotations

from python.helpers.demo_request_store import list_demo_requests
from python.helpers.tool import Response, Tool


class DemoRequestList(Tool):
    async def execute(self, **kwargs) -> Response:
        args = self.args or {}
        try:
            limit = int(args.get("limit", 25))
        except (TypeError, ValueError):
            limit = 25

        rows = list_demo_requests(limit=limit)
        if not rows:
            return Response(
                message="No demo requests found.",
                break_loop=False,
                additional={"demo_requests": []},
            )

        lines = [f"Recent demo requests ({len(rows)}):"]
        for row in rows:
            lines.append(f"- {row.get('id')} | {row.get('company')} | {row.get('email')}")
        return Response(
            message="\n".join(lines),
            break_loop=False,
            additional={"demo_requests": rows},
        )
