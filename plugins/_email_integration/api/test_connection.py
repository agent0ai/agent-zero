"""Test IMAP/SMTP connection for an email handler config."""

from helpers.api import ApiHandler, Request
from helpers.errors import format_error

from plugins._email_integration.helpers.imap_client import (
    connect_imap,
    disconnect_imap,
    get_highest_uid,
)
from plugins._email_integration.helpers.smtp_client import SmtpConfig, test_smtp, send_reply


class TestConnection(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        handler = input.get("handler", {})
        results: list[dict] = []
        account_type = handler.get("account_type", "imap")

        if account_type == "imap":
            await self._test_imap(handler, results)
        await self._test_smtp(handler, results)
        if all(r["ok"] for r in results):
            await self._test_send(handler, results)

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

    def _smtp_config(self, handler: dict) -> SmtpConfig:
        smtp_server = handler.get("smtp_server") or handler.get("imap_server", "")
        return SmtpConfig(
            server=smtp_server,
            port=int(handler.get("smtp_port", 587)),
            username=handler.get("username", ""),
            password=handler.get("password", ""),
        )

    async def _test_smtp(self, handler: dict, results: list[dict]):
        try:
            error = await test_smtp(self._smtp_config(handler))
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

    async def _test_send(self, handler: dict, results: list[dict]):
        try:
            error = await send_reply(
                config=self._smtp_config(handler),
                to=handler.get("username", ""),
                subject="Agent Zero - Connection Test",
                body="This is a test email from Agent Zero email integration.",
            )
            if error:
                results.append({"test": "Send", "ok": False, "message": error})
            else:
                results.append({
                    "test": "Send",
                    "ok": True,
                    "message": "Test email sent to self",
                })
        except Exception as e:
            results.append({
                "test": "Send",
                "ok": False,
                "message": format_error(e),
            })
