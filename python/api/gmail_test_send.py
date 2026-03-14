"""
Gmail Test Send API Handler
Sends a test email via Gmail API to verify configuration
"""

from python.helpers import settings
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.gmail_api_client import GmailAPIClient


class GmailTestSend(ApiHandler):
    """Send a Gmail API test email"""

    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Send a test email via Gmail API

        Input:
            account_name: Gmail account name (optional if only one configured)
            to: Recipient email address (optional; defaults to account email if known)
            subject: Optional subject line
            body: Optional email body

        Returns:
            success: True if send succeeded
            message_id: Gmail message ID
            thread_id: Gmail thread ID
        """
        try:
            account_name = input.get("account_name")
            to = input.get("to")
            subject = input.get("subject") or "Agent Jumbo Gmail Test"
            body = input.get("body") or "This is a test email from Agent Jumbo Gmail UI."

            current_settings = settings.get_settings()
            gmail_accounts = current_settings.get("gmail_accounts", {})

            if account_name:
                account_name = account_name.strip()

            if not account_name:
                if len(gmail_accounts) == 0:
                    return Response("No Gmail accounts configured", 400)
                if len(gmail_accounts) == 1:
                    account_name = next(iter(gmail_accounts.keys()))
                else:
                    return Response("account_name is required when multiple accounts exist", 400)

            account_info = gmail_accounts.get(account_name, {})
            if not to:
                to = account_info.get("email")

            if not to:
                return Response("to is required (recipient email address)", 400)

            client = GmailAPIClient(account_name)
            result = client.send_email(to=[to] if isinstance(to, str) else to, subject=subject, body=body, html=False)

            if not result.get("success"):
                return Response(result.get("error") or "Failed to send test email", 500)

            return {
                "success": True,
                "message_id": result.get("message_id"),
                "thread_id": result.get("thread_id"),
                "to": result.get("to"),
                "account_name": account_name,
            }

        except Exception as e:
            return Response(f"Failed to send test email: {e!s}", 500)

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]
