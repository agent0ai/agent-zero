import asyncio
import email
import os
import re
import uuid
from dataclasses import dataclass
from email.header import decode_header
from email.message import Message as EmailMessage
from fnmatch import fnmatch
from typing import Any, Dict, List, Optional, Tuple

import html2text
from bs4 import BeautifulSoup
from imapclient import IMAPClient

from python.helpers import files
from python.helpers.errors import RepairableException, format_error
from python.helpers.print_style import PrintStyle


@dataclass
class Message:
    """Email message representation with sender, subject, body, and attachments."""
    sender: str
    subject: str
    body: str
    attachments: List[str]


class EmailClient:
    """
    Async email client for reading messages from IMAP and Exchange servers.

    """

    def __init__(
        self,
        account_type: str = "imap",
        server: str = "",
        port: int = 993,
        username: str = "",
        password: str = "",
        options: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize email client with connection parameters.

        Args:
            account_type: Type of account - "imap" or "exchange"
            server: Mail server address (e.g., "imap.gmail.com")
            port: Server port (default 993 for IMAP SSL)
            username: Email account username
            password: Email account password
            options: Optional configuration dict with keys:
                - ssl: Use SSL/TLS (default: True)
                - timeout: Connection timeout in seconds (default: 30)
        """
        self.account_type = account_type.lower()
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.options = options or {}

        # Default options
        self.ssl = self.options.get("ssl", True)
        self.timeout = self.options.get("timeout", 30)

        self.client: Optional[IMAPClient] = None
        self.exchange_account = None

    async def connect(self) -> None:
        """Establish connection to email server."""
        try:
            if self.account_type == "imap":
                await self._connect_imap()
            elif self.account_type == "exchange":
                await self._connect_exchange()
            else:
                raise RepairableException(
                    f"Unsupported account type: {self.account_type}. "
                    "Supported types: 'imap', 'exchange'"
                )
        except Exception as e:
            err = format_error(e)
            PrintStyle.error(f"Failed to connect to email server: {err}")
            raise RepairableException(f"Email connection failed: {err}") from e

    async def _connect_imap(self) -> None:
        """Establish IMAP connection."""
        loop = asyncio.get_event_loop()

        def _sync_connect():
            client = IMAPClient(self.server, port=self.port, ssl=self.ssl, timeout=self.timeout)
            # Increase line length limit to handle large emails (default is 10000)
            # This fixes "line too long" errors for emails with large headers or embedded content
            client._imap._maxline = 100000
            client.login(self.username, self.password)
            return client

        self.client = await loop.run_in_executor(None, _sync_connect)
        PrintStyle.standard(f"Connected to IMAP server: {self.server}")

    async def _connect_exchange(self) -> None:
        """Establish Exchange connection."""
        try:
            from exchangelib import Account, Configuration, Credentials, DELEGATE

            loop = asyncio.get_event_loop()

            def _sync_connect():
                creds = Credentials(username=self.username, password=self.password)
                config = Configuration(server=self.server, credentials=creds)
                return Account(
                    primary_smtp_address=self.username,
                    config=config,
                    autodiscover=False,
                    access_type=DELEGATE
                )

            self.exchange_account = await loop.run_in_executor(None, _sync_connect)
            PrintStyle.standard(f"Connected to Exchange server: {self.server}")
        except ImportError as e:
            raise RepairableException(
                "exchangelib not installed. Install with: pip install exchangelib>=5.4.3"
            ) from e

    async def disconnect(self) -> None:
        """Clean up connection."""
        try:
            if self.client:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.client.logout)
                self.client = None
                PrintStyle.standard("Disconnected from IMAP server")
            elif self.exchange_account:
                self.exchange_account = None
                PrintStyle.standard("Disconnected from Exchange server")
        except Exception as e:
            PrintStyle.error(f"Error during disconnect: {format_error(e)}")

    async def read_messages(
        self,
        download_folder: str,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Message]:
        """
        Read messages based on filter criteria.

        Args:
            download_folder: Folder to save attachments (relative to /a0/)
            filter: Filter criteria dict with keys:
                - unread: Boolean to filter unread messages (default: True)
                - sender: Sender pattern with wildcards (e.g., "*@company.com")
                - subject: Subject pattern with wildcards (e.g., "*invoice*")
                - since_date: Optional datetime for date filtering

        Returns:
            List of Message objects with attachments saved to download_folder
        """
        filter = filter or {}

        if self.account_type == "imap":
            return await self._fetch_imap_messages(download_folder, filter)
        elif self.account_type == "exchange":
            return await self._fetch_exchange_messages(download_folder, filter)
        else:
            raise RepairableException(f"Unsupported account type: {self.account_type}")

    async def _fetch_imap_messages(
        self,
        download_folder: str,
        filter: Dict[str, Any],
    ) -> List[Message]:
        """Fetch messages from IMAP server."""
        if not self.client:
            raise RepairableException("IMAP client not connected. Call connect() first.")

        loop = asyncio.get_event_loop()
        messages: List[Message] = []

        def _sync_fetch():
            # Select inbox
            self.client.select_folder("INBOX")

            # Build search criteria
            search_criteria = []
            if filter.get("unread", True):
                search_criteria.append("UNSEEN")

            if filter.get("since_date"):
                since_date = filter["since_date"]
                search_criteria.append(["SINCE", since_date])

            # Search for messages
            if not search_criteria:
                search_criteria = ["ALL"]

            message_ids = self.client.search(search_criteria)
            return message_ids

        message_ids = await loop.run_in_executor(None, _sync_fetch)

        if not message_ids:
            PrintStyle.hint("No messages found matching criteria")
            return messages

        PrintStyle.standard(f"Found {len(message_ids)} messages")

        # Fetch and process messages
        for msg_id in message_ids:
            try:
                msg = await self._fetch_and_parse_imap_message(msg_id, download_folder, filter)
                if msg:
                    messages.append(msg)
            except Exception as e:
                PrintStyle.error(f"Error processing message {msg_id}: {format_error(e)}")
                continue

        return messages

    async def _fetch_and_parse_imap_message(
        self,
        msg_id: int,
        download_folder: str,
        filter: Dict[str, Any],
    ) -> Optional[Message]:
        """Fetch and parse a single IMAP message with retry logic for large messages."""
        loop = asyncio.get_event_loop()

        def _sync_fetch():
            try:
                # Try standard RFC822 fetch first
                return self.client.fetch([msg_id], ["RFC822"])[msg_id]
            except Exception as e:
                error_msg = str(e).lower()
                # If "line too long" error, try fetching in parts
                if "line too long" in error_msg or "fetch_failed" in error_msg:
                    PrintStyle.warning(f"Message {msg_id} too large for standard fetch, trying alternative method")
                    # Fetch headers and body separately to avoid line length issues
                    try:
                        envelope = self.client.fetch([msg_id], ["BODY.PEEK[]"])[msg_id]
                        return envelope
                    except Exception as e2:
                        PrintStyle.error(f"Alternative fetch also failed for message {msg_id}: {format_error(e2)}")
                        raise
                raise

        try:
            raw_msg = await loop.run_in_executor(None, _sync_fetch)

            # Extract email data from response
            if b"RFC822" in raw_msg:
                email_data = raw_msg[b"RFC822"]
            elif b"BODY[]" in raw_msg:
                email_data = raw_msg[b"BODY[]"]
            else:
                PrintStyle.error(f"Unexpected response format for message {msg_id}")
                return None

            email_msg = email.message_from_bytes(email_data)

            # Apply sender filter
            sender = self._decode_header(email_msg.get("From", ""))
            if filter.get("sender") and not fnmatch(sender, filter["sender"]):
                return None

            # Apply subject filter
            subject = self._decode_header(email_msg.get("Subject", ""))
            if filter.get("subject") and not fnmatch(subject, filter["subject"]):
                return None

            # Parse message
            return await self._parse_message(email_msg, download_folder)

        except Exception as e:
            PrintStyle.error(f"Failed to fetch/parse message {msg_id}: {format_error(e)}")
            return None

    async def _fetch_exchange_messages(
        self,
        download_folder: str,
        filter: Dict[str, Any],
    ) -> List[Message]:
        """Fetch messages from Exchange server."""
        if not self.exchange_account:
            raise RepairableException("Exchange account not connected. Call connect() first.")

        from exchangelib import Q

        loop = asyncio.get_event_loop()
        messages: List[Message] = []

        def _sync_fetch():
            # Build query
            query = None
            if filter.get("unread", True):
                query = Q(is_read=False)

            if filter.get("sender"):
                sender_pattern = filter["sender"].replace("*", "")
                sender_q = Q(sender__contains=sender_pattern)
                query = query & sender_q if query else sender_q

            if filter.get("subject"):
                subject_pattern = filter["subject"].replace("*", "")
                subject_q = Q(subject__contains=subject_pattern)
                query = query & subject_q if query else subject_q

            # Fetch messages from inbox
            inbox = self.exchange_account.inbox
            items = inbox.filter(query) if query else inbox.all()
            return list(items)

        exchange_messages = await loop.run_in_executor(None, _sync_fetch)

        PrintStyle.standard(f"Found {len(exchange_messages)} Exchange messages")

        # Process messages
        for ex_msg in exchange_messages:
            try:
                msg = await self._parse_exchange_message(ex_msg, download_folder)
                if msg:
                    messages.append(msg)
            except Exception as e:
                PrintStyle.error(f"Error processing Exchange message: {format_error(e)}")
                continue

        return messages

    async def _parse_exchange_message(
        self,
        ex_msg,
        download_folder: str,
    ) -> Message:
        """Parse an Exchange message."""
        loop = asyncio.get_event_loop()

        def _get_body():
            return str(ex_msg.text_body or ex_msg.body or "")

        body = await loop.run_in_executor(None, _get_body)

        # Process HTML if present
        if ex_msg.body and str(ex_msg.body).strip().startswith("<"):
            body = self._html_to_text(str(ex_msg.body))

        # Save attachments
        attachment_paths = []
        if ex_msg.attachments:
            for attachment in ex_msg.attachments:
                if hasattr(attachment, "content"):
                    path = await self._save_attachment_bytes(
                        attachment.name,
                        attachment.content,
                        download_folder
                    )
                    attachment_paths.append(path)

        return Message(
            sender=str(ex_msg.sender.email_address) if ex_msg.sender else "",
            subject=str(ex_msg.subject or ""),
            body=body,
            attachments=attachment_paths
        )

    async def _parse_message(
        self,
        email_msg: EmailMessage,
        download_folder: str,
    ) -> Message:
        """
        Parse email message and extract content with inline attachments.

        Processes multipart messages, converts HTML to text, and maintains
        positional context for inline attachments.
        """
        sender = self._decode_header(email_msg.get("From", ""))
        subject = self._decode_header(email_msg.get("Subject", ""))

        # Extract body and attachments
        body = ""
        attachment_paths: List[str] = []
        cid_map: Dict[str, str] = {}  # Map Content-ID to file paths
        body_parts: List[str] = []  # Track parts in order

        if email_msg.is_multipart():
            # Process parts in order to maintain attachment positions
            for part in email_msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip multipart containers
                if part.get_content_maintype() == "multipart":
                    continue

                # Handle attachments
                if "attachment" in content_disposition or part.get("Content-ID"):
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        content = part.get_payload(decode=True)
                        if content:
                            path = await self._save_attachment_bytes(
                                filename, content, download_folder
                            )
                            attachment_paths.append(path)

                            # Map Content-ID for inline images
                            cid = part.get("Content-ID")
                            if cid:
                                cid = cid.strip("<>")
                                cid_map[cid] = path

                            # Add positional marker for non-cid attachments
                            # (cid attachments are positioned via HTML references)
                            if not cid and body_parts:
                                body_parts.append(f"\n[file://{path}]\n")

                # Handle body text
                elif content_type == "text/plain":
                    if not body:  # Use first text/plain as primary body
                        charset = part.get_content_charset() or "utf-8"
                        body = part.get_payload(decode=True).decode(charset, errors="ignore")
                        body_parts.append(body)

                elif content_type == "text/html":
                    if not body:  # Use first text/html as primary body if no text/plain
                        charset = part.get_content_charset() or "utf-8"
                        html_content = part.get_payload(decode=True).decode(charset, errors="ignore")
                        body = self._html_to_text(html_content, cid_map)
                        body_parts.append(body)

            # Combine body parts if we built them up
            if len(body_parts) > 1:
                body = "".join(body_parts)
        else:
            # Single part message
            content_type = email_msg.get_content_type()
            charset = email_msg.get_content_charset() or "utf-8"
            content = email_msg.get_payload(decode=True)
            if content:
                if content_type == "text/html":
                    body = self._html_to_text(content.decode(charset, errors="ignore"), cid_map)
                else:
                    body = content.decode(charset, errors="ignore")

        return Message(
            sender=sender,
            subject=subject,
            body=body,
            attachments=attachment_paths
        )

    def _html_to_text(self, html_content: str, cid_map: Optional[Dict[str, str]] = None) -> str:
        """
        Convert HTML to plain text with inline attachment references.

        Replaces inline images with [file:///a0/...] markers to maintain
        positional context.
        """
        cid_map = cid_map or {}

        # Replace cid: references with file paths before conversion
        if cid_map:
            soup = BeautifulSoup(html_content, "html.parser")
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if src.startswith("cid:"):
                    cid = src[4:]  # Remove "cid:" prefix
                    if cid in cid_map:
                        # Replace with file path marker
                        file_marker = f"[file://{cid_map[cid]}]"
                        img.replace_with(soup.new_string(file_marker))
            html_content = str(soup)

        # Convert HTML to text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.body_width = 0  # Don't wrap lines

        text = h.handle(html_content)

        # Clean up extra whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 consecutive newlines
        text = text.strip()

        return text

    async def _save_attachment_bytes(
        self,
        filename: str,
        content: bytes,
        download_folder: str,
    ) -> str:
        """
        Save attachment to disk and return absolute path.

        Uses Agent Zero's file helpers for path management.
        """
        # Sanitize filename
        filename = files.safe_file_name(filename)

        # Generate unique filename if needed
        unique_id = uuid.uuid4().hex[:8]
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{unique_id}{ext}"

        # Build relative path and save
        relative_path = os.path.join(download_folder, unique_filename)
        files.write_file_bin(relative_path, content)

        # Return absolute path
        abs_path = files.get_abs_path(relative_path)
        return abs_path

    def _decode_header(self, header: str) -> str:
        """Decode email header handling various encodings."""
        if not header:
            return ""

        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or "utf-8", errors="ignore"))
            else:
                decoded_parts.append(str(part))

        return " ".join(decoded_parts)


async def read_messages(
    account_type: str = "imap",
    server: str = "",
    port: int = 993,
    username: str = "",
    password: str = "",
    download_folder: str = "tmp/email",
    options: Optional[Dict[str, Any]] = None,
    filter: Optional[Dict[str, Any]] = None,
) -> List[Message]:
    """
    Convenience wrapper for reading email messages.

    Automatically handles connection and disconnection.

    Args:
        account_type: "imap" or "exchange"
        server: Mail server address
        port: Server port (default 993 for IMAP SSL)
        username: Email username
        password: Email password
        download_folder: Folder to save attachments (relative to /a0/)
        options: Optional configuration dict
        filter: Filter criteria dict

    Returns:
        List of Message objects

    Example:
        from python.helpers.email_client import read_messages
        messages = await read_messages(
            server="imap.gmail.com",
            port=993,
            username=secrets.get("EMAIL_USER"),
            password=secrets.get("EMAIL_PASSWORD"),
            download_folder="tmp/email/inbox",
            filter={"unread": True, "sender": "*@company.com"}
        )
    """
    client = EmailClient(
        account_type=account_type,
        server=server,
        port=port,
        username=username,
        password=password,
        options=options,
    )

    try:
        await client.connect()
        messages = await client.read_messages(download_folder, filter)
        return messages
    finally:
        await client.disconnect()
