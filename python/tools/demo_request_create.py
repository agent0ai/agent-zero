from __future__ import annotations

from typing import Any

from python.helpers.demo_request_store import create_demo_request
from python.helpers.tool import Response, Tool


class DemoRequestCreate(Tool):
    async def execute(self, **kwargs) -> Response:
        payload: dict[str, Any] = dict(self.args or {})
        company = str(payload.get("company", "")).strip()
        email = str(payload.get("email", "")).strip()

        if not company or not email:
            return Response(
                message="Missing required fields: company and email",
                break_loop=False,
            )

        record = create_demo_request(payload)
        return Response(
            message=f"Demo request created: {record['id']}",
            break_loop=False,
            additional={"demo_request": record},
        )
