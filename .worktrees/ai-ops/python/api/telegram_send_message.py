from python.helpers.api import ApiHandler, Request, Response
from python.helpers import dotenv
from python.helpers.telegram_client import send_message


class TelegramSendMessage(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        text = input.get("text", "")
        if not text:
            return {"success": False, "error": "text is required"}

        chat_id = input.get("chat_id") or dotenv.get_dotenv_value("TELEGRAM_CHAT_ID", "")
        if not chat_id:
            return {"success": False, "error": "chat_id is required"}

        token = dotenv.get_dotenv_value("TELEGRAM_BOT_TOKEN", "")
        if not token:
            return {"success": False, "error": "bot token is required"}

        try:
            result = send_message(token, str(chat_id), text)
            return {"success": True, "result": result}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
