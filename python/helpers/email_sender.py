"""
Async SMTP Email Sender for Agent Jumbo
Supports Gmail and other SMTP providers
"""

import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib


class EmailSender:
    """Async SMTP email sender compatible with Agent Jumbo"""

    def __init__(self, server: str, port: int, username: str, password: str, use_tls: bool = True):
        """
        Initialize SMTP email sender

        Args:
            server: SMTP server address (e.g., smtp.gmail.com)
            port: SMTP port (587 for TLS, 465 for SSL, 25 for plain)
            username: Email account username
            password: Email account password or app password
            use_tls: Whether to use STARTTLS (default: True)
        """
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[str] | None = None,
        html: bool = False,
        from_name: str | None = None,
    ) -> dict:
        """
        Send email with optional attachments

        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body content
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            attachments: Optional list of file paths to attach
            html: Whether body is HTML (default: False for plain text)
            from_name: Optional display name for sender

        Returns:
            Dict with success status and message_id
        """
        # Create message
        msg = MIMEMultipart()

        # Set sender
        if from_name:
            msg["From"] = f"{from_name} <{self.username}>"
        else:
            msg["From"] = self.username

        msg["To"] = ", ".join(to)
        msg["Subject"] = subject

        if cc:
            msg["Cc"] = ", ".join(cc)

        # Add body
        body_type = "html" if html else "plain"
        msg.attach(MIMEText(body, body_type, "utf-8"))

        # Add attachments
        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Attachment not found: {file_path}")

                with open(file_path, "rb") as f:
                    filename = os.path.basename(file_path)
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                    msg.attach(part)

        # Build recipient list (to + cc + bcc)
        all_recipients = to.copy()
        if cc:
            all_recipients.extend(cc)
        if bcc:
            all_recipients.extend(bcc)

        # Send email
        try:
            if self.use_tls:
                # Use STARTTLS (port 587)
                await aiosmtplib.send(
                    msg,
                    hostname=self.server,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    start_tls=True,
                )
            else:
                # Direct SSL connection (port 465) or plain (port 25)
                await aiosmtplib.send(
                    msg,
                    hostname=self.server,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    use_tls=(self.port == 465),
                )

            return {
                "success": True,
                "message_id": msg.get("Message-ID", "unknown"),
                "recipients": len(all_recipients),
                "to": to,
                "subject": subject,
            }

        except aiosmtplib.SMTPException as e:
            return {"success": False, "error": str(e), "error_type": type(e).__name__}
        except Exception as e:
            return {"success": False, "error": str(e), "error_type": "UnexpectedError"}

    async def send_bulk_emails(self, recipients: list[dict], delay_seconds: float = 0.1) -> dict:
        """
        Send multiple emails with rate limiting

        Args:
            recipients: List of dicts with email parameters (to, subject, body, etc.)
            delay_seconds: Delay between sends to avoid rate limits

        Returns:
            Dict with success count, failed count, and details
        """
        import asyncio

        results = {"total": len(recipients), "successful": 0, "failed": 0, "details": []}

        for recipient in recipients:
            result = await self.send_email(**recipient)

            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1

            results["details"].append(result)

            # Rate limiting delay
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)

        return results

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Basic email validation

        Args:
            email: Email address to validate

        Returns:
            True if email appears valid
        """
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe attachment handling

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        import os
        import re

        # Normalize path separators and collapse traversal into underscores.
        normalized = filename.replace("\\", "/")
        parts = [part for part in normalized.split("/") if part and part not in (".", "..")]
        if parts:
            filename = "_".join(parts)
        else:
            filename = os.path.basename(normalized)

        # Replace any remaining path separators with underscores.
        filename = filename.replace("/", "_").replace("\\", "_")

        # Remove unsafe characters but keep spaces, dots, hyphens, and underscores.
        safe_name = re.sub(r"[^\w\s.-]", "", filename).strip()

        return safe_name or "attachment"
