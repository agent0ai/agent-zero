import asyncio
import threading
import unittest
from unittest.mock import AsyncMock, patch

from flask import Flask

from helpers import api, cache
from plugins._telegram_integration.helpers import bot_manager as bm


class TelegramWebhookSecurityTests(unittest.TestCase):
    def test_http_authentication_before_real_dispatch(self):
        received = []

        async def receive(message):
            received.append((message.from_user.id, message.text))

        with patch.object(bm, "_bots", {}):
            instance = bm.create_bot("security_test", "123456:test", receive, receive)
            app = Flask(__name__)
            api.register_api_route(app, threading.Lock())
            client = app.test_client()
            payload = {"update_id": 1, "message": {
                "message_id": 1, "date": 1700000000,
                "from": {"id": 424242, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 424242, "type": "private"},
                "text": "POC_CONFIRMED",
            }}
            try:
                for active, secret, header, expected in [
                    (False, "", "", 403),
                    (False, "x" * 32, "x" * 32, 403),
                    (True, "", "", 403),
                    (True, "x" * 32, "", 403),
                    (True, "x" * 32, "wrong", 403),
                    (True, "x" * 32, "é", 403),
                    (True, "x" * 32, "x" * 32, 200),
                ]:
                    with self.subTest(active=active, header=header, expected=expected):
                        instance.webhook_active = active
                        instance.webhook_secret = secret
                        received.clear()
                        response = client.post(
                            "/api/plugins/_telegram_integration/webhook?bot=security_test",
                            json=payload,
                            headers={"X-Telegram-Bot-Api-Secret-Token": header},
                        )
                        self.assertEqual(response.status_code, expected)
                        self.assertEqual(received, [(424242, "POC_CONFIRMED")] if expected == 200 else [])
            finally:
                cache.clear(api.CACHE_AREA)
                asyncio.run(instance.bot.session.close())

    def test_webhook_setup_and_polling_revoke_authentication(self):
        async def receive(message):
            pass

        async def run():
            with patch.object(bm, "_bots", {}):
                instance = bm.create_bot("security_test", "123456:test", receive, receive)
                try:
                    with patch.object(instance.bot, "set_webhook", new_callable=AsyncMock) as register:
                        for secret in ("", "short", "é" * 32, "x" * 257):
                            with self.subTest(secret=secret):
                                with self.assertRaises(ValueError):
                                    await bm.setup_webhook(instance, "https://example.invalid", secret)
                                self.assertFalse(instance.webhook_active)
                        register.assert_not_awaited()
                        await bm.setup_webhook(instance, "https://example.invalid", "x" * 32)
                        self.assertEqual(register.await_args.kwargs["secret_token"], "x" * 32)
                        self.assertTrue(instance.webhook_active)
                    with patch.object(instance.bot, "delete_webhook", new_callable=AsyncMock), patch.object(
                        instance.dispatcher, "start_polling", new_callable=AsyncMock
                    ):
                        task = await bm.start_polling(instance)
                        self.assertFalse(instance.webhook_active)
                        self.assertEqual(instance.webhook_secret, "")
                        await task
                finally:
                    await instance.bot.session.close()
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
