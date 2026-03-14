"""
Email Tool for Agent Jumbo
Provides email send/read/search capabilities with SMTP and IMAP
"""

import os

from python.helpers import files
from python.helpers.email_client import read_messages
from python.helpers.email_sender import EmailSender
from python.helpers.tool import Response, Tool


class Email(Tool):
    """
    Email operations tool for Agent Jumbo.
    Supports send (SMTP), read (IMAP), and search operations.
    Integrates with customer_lifecycle and virtual_team for automation.
    """

    async def execute(self, **kwargs):
        """Execute email action"""

        action = self.args.get("action", "").lower()

        # Route to appropriate action handler
        if action == "send":
            return await self._send_email()
        elif action == "read":
            return await self._read_emails()
        elif action == "search":
            return await self._search_emails()
        elif action == "send_bulk":
            return await self._send_bulk_emails()
        else:
            return Response(
                message=f"Unknown email action: {action}. Available actions: send, read, search, send_bulk",
                break_loop=False,
            )

    async def _send_email(self):
        """Send email via SMTP"""
        try:
            # Get SMTP configuration from environment
            smtp_server = os.getenv("GMAIL_SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("GMAIL_SMTP_PORT", "587"))
            from_email = os.getenv("GMAIL_FROM_EMAIL")
            app_password = os.getenv("GMAIL_APP_PASSWORD")

            if not from_email or not app_password:
                return Response(
                    message="Email credentials not configured. Please set GMAIL_FROM_EMAIL and GMAIL_APP_PASSWORD in environment variables.",
                    break_loop=False,
                )

            # Validate recipients
            to_list = self.args.get("to", [])
            if isinstance(to_list, str):
                to_list = [to_list]

            if not to_list:
                return Response(message="No recipients specified. Please provide 'to' parameter.", break_loop=False)

            # Validate email addresses
            invalid_emails = [email for email in to_list if not EmailSender.validate_email(email)]
            if invalid_emails:
                return Response(message=f"Invalid email addresses: {', '.join(invalid_emails)}", break_loop=False)

            # Create sender
            sender = EmailSender(
                server=smtp_server, port=smtp_port, username=from_email, password=app_password, use_tls=True
            )

            # Send email
            result = await sender.send_email(
                to=to_list,
                subject=self.args.get("subject", ""),
                body=self.args.get("body", ""),
                cc=self.args.get("cc"),
                bcc=self.args.get("bcc"),
                attachments=self.args.get("attachments"),
                html=self.args.get("html", False),
                from_name=self.args.get("from_name", "Agent Jumbo"),
            )

            if result.get("success"):
                message = "✅ Email sent successfully!\n\n"
                message += f"**Recipients:** {', '.join(result['to'])}\n"
                message += f"**Subject:** {result['subject']}\n"
                message += f"**Total Recipients:** {result['recipients']}\n"

                if self.args.get("attachments"):
                    message += f"**Attachments:** {len(self.args.get('attachments'))} file(s)\n"
            else:
                message = "❌ Email send failed\n\n"
                message += f"**Error:** {result.get('error', 'Unknown error')}\n"
                message += f"**Error Type:** {result.get('error_type', 'Unknown')}\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Email send error: {e!s}", break_loop=False)

    async def _read_emails(self):
        """Read emails via IMAP (using existing implementation)"""
        try:
            # Get IMAP configuration
            imap_server = os.getenv("GMAIL_IMAP_SERVER", "imap.gmail.com")
            imap_port = int(os.getenv("GMAIL_IMAP_PORT", "993"))
            username = os.getenv("GMAIL_FROM_EMAIL")
            password = os.getenv("GMAIL_APP_PASSWORD")

            if not username or not password:
                return Response(
                    message="Email credentials not configured. Please set GMAIL_FROM_EMAIL and GMAIL_APP_PASSWORD.",
                    break_loop=False,
                )

            # Set download folder
            download_folder = self.args.get("download_folder", "tmp/email/inbox")
            download_path = files.get_abs_path(download_folder)

            # Read messages using existing IMAP client
            messages = await read_messages(
                account_type="imap",
                server=imap_server,
                port=imap_port,
                username=username,
                password=password,
                download_folder=download_path,
                filter=self.args.get("filter", {"unread": True}),
            )

            if not messages:
                return Response(message="No messages found matching the criteria.", break_loop=False)

            # Format results
            result = f"📧 Found {len(messages)} message(s):\n\n"

            for i, msg in enumerate(messages, 1):
                result += f"**{i}. From:** {msg.sender}\n"
                result += f"   **Subject:** {msg.subject}\n"
                result += f"   **Date:** {msg.date}\n"

                # Truncate body for display
                body_preview = msg.body[:200].replace("\n", " ") if msg.body else ""
                if len(msg.body) > 200:
                    body_preview += "..."
                result += f"   **Preview:** {body_preview}\n"

                if msg.attachments:
                    result += f"   **Attachments:** {len(msg.attachments)} file(s)\n"
                    for att in msg.attachments:
                        result += f"      - {att}\n"

                result += "\n"

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Email read error: {e!s}", break_loop=False)

    async def _search_emails(self):
        """Search emails with advanced filters"""
        try:
            # Use read functionality with custom filter
            search_filter = {}

            # Build filter from search parameters
            if self.args.get("sender"):
                search_filter["sender"] = self.args.get("sender")

            if self.args.get("subject"):
                search_filter["subject"] = self.args.get("subject")

            if self.args.get("unread_only"):
                search_filter["unread"] = True

            if self.args.get("since_date"):
                search_filter["since_date"] = self.args.get("since_date")

            # Store original filter and temporarily replace
            original_filter = self.args.get("filter", {})
            self.args["filter"] = search_filter

            # Use read functionality
            result = await self._read_emails()

            # Restore original filter
            self.args["filter"] = original_filter

            return result

        except Exception as e:
            return Response(message=f"❌ Email search error: {e!s}", break_loop=False)

    async def _send_bulk_emails(self):
        """Send multiple emails with rate limiting"""
        try:
            # Get SMTP configuration
            smtp_server = os.getenv("GMAIL_SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("GMAIL_SMTP_PORT", "587"))
            from_email = os.getenv("GMAIL_FROM_EMAIL")
            app_password = os.getenv("GMAIL_APP_PASSWORD")

            if not from_email or not app_password:
                return Response(message="Email credentials not configured.", break_loop=False)

            # Get recipient list
            recipients = self.args.get("recipients", [])
            if not recipients:
                return Response(message="No recipients provided. Please specify 'recipients' list.", break_loop=False)

            # Create sender
            sender = EmailSender(
                server=smtp_server, port=smtp_port, username=from_email, password=app_password, use_tls=True
            )

            # Send bulk emails
            delay = self.args.get("delay_seconds", 0.5)  # Default 0.5s delay
            result = await sender.send_bulk_emails(recipients, delay_seconds=delay)

            message = "📧 Bulk Email Results:\n\n"
            message += f"**Total:** {result['total']}\n"
            message += f"**Successful:** {result['successful']} ✅\n"
            message += f"**Failed:** {result['failed']} ❌\n\n"

            # Show details of any failures
            if result["failed"] > 0:
                message += "**Failed Emails:**\n"
                for detail in result["details"]:
                    if not detail.get("success"):
                        message += f"  - To: {detail.get('to', 'unknown')}\n"
                        message += f"    Error: {detail.get('error', 'unknown')}\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Bulk email error: {e!s}", break_loop=False)
