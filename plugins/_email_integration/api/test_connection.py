"""Test IMAP/SMTP connection for an email handler config."""

from helpers.api import ApiHandler, Request
from helpers.errors import format_error

from plugins._email_integration.helpers.imap_client import (
    connect_imap,
    disconnect_imap,
    get_highest_uid,
)
from plugins._email_integration.helpers.smtp_client import SmtpConfig, test_smtp


class TestConnection(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        handler = input.get("handler", {})
        results: list[dict] = []
        account_type = handler.get("account_type", "imap")

        if account_type == "imap":
            await self._test_imap(handler, results)
        await self._test_smtp(handler, results)

        ok = all(r["ok"] for r in results)
        return {"success": ok, "results": results}

    async def _test_imap(self, handler: dict, results: list[dict]):
        try:
            client = await connect_imap(
                server=handler.get("imap_server", ""),
                port=int(handler.get("imap_port", 993)),
                username=handler.get("username", ""),
                password=handler.get("password", ""),
            )
            uid = await get_highest_uid(client)
            await disconnect_imap(client)
            results.append({
                "test": "IMAP",
                "ok": True,
                "message": f"Connected, highest UID: {uid}",
            })
        except Exception as e:
            results.append({
                "test": "IMAP",
                "ok": False,
                "message": format_error(e),
            })

    async def _test_smtp(self, handler: dict, results: list[dict]):
        try:
            smtp_server = handler.get("smtp_server") or handler.get("imap_server", "")
            cfg = SmtpConfig(
                server=smtp_server,
                port=int(handler.get("smtp_port", 587)),
                username=handler.get("username", ""),
                password=handler.get("password", ""),
            )
            error = await test_smtp(cfg)
            if error:
                results.append({"test": "SMTP", "ok": False, "message": error})
            else:
                results.append({
                    "test": "SMTP",
                    "ok": True,
                    "message": "Authenticated successfully",
                })
        except Exception as e:
            results.append({
                "test": "SMTP",
                "ok": False,
                "message": format_error(e),
            })
