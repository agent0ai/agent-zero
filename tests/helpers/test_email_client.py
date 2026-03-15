"""Comprehensive unit tests for python/helpers/email_client.py — email parsing, SMTP/IMAP."""

import os
import sys
from pathlib import Path
from email.message import EmailMessage as StdEmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Message dataclass ---


class TestMessageDataclass:
    def test_message_creation(self):
        from python.helpers.email_client import Message

        msg = Message(
            sender="alice@example.com",
            subject="Test",
            body="Hello",
            attachments=["/a0/usr/email/file.pdf"],
        )
        assert msg.sender == "alice@example.com"
        assert msg.subject == "Test"
        assert msg.body == "Hello"
        assert msg.attachments == ["/a0/usr/email/file.pdf"]

    def test_message_empty_attachments(self):
        from python.helpers.email_client import Message

        msg = Message(sender="", subject="", body="", attachments=[])
        assert msg.attachments == []


# --- EmailClient.__init__ ---


class TestEmailClientInit:
    def test_init_imap_defaults(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(
            account_type="imap",
            server="imap.gmail.com",
            username="user",
            password="pass",
        )
        assert client.account_type == "imap"
        assert client.server == "imap.gmail.com"
        assert client.port == 993
        assert client.username == "user"
        assert client.password == "pass"
        assert client.ssl is True
        assert client.timeout == 30
        assert client.client is None

    def test_init_normalizes_account_type(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(account_type="IMAP", server="x", username="u", password="p")
        assert client.account_type == "imap"

    def test_init_with_options(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(
            account_type="imap",
            server="imap.example.com",
            port=143,
            username="u",
            password="p",
            options={"ssl": False, "timeout": 60},
        )
        assert client.ssl is False
        assert client.timeout == 60


# --- EmailClient.connect ---


class TestEmailClientConnect:
    @pytest.mark.asyncio
    async def test_connect_imap_success(self):
        from python.helpers.email_client import EmailClient

        mock_client = MagicMock()
        with patch("python.helpers.email_client.IMAPClient", return_value=mock_client):
            with patch("python.helpers.email_client.PrintStyle"):
                client = EmailClient(
                    account_type="imap",
                    server="imap.gmail.com",
                    username="u",
                    password="p",
                )
                await client.connect()
        assert client.client is mock_client

    @pytest.mark.asyncio
    async def test_connect_unsupported_account_type(self):
        from python.helpers.email_client import EmailClient
        from python.helpers.errors import RepairableException

        with patch("python.helpers.email_client.PrintStyle"):
            client = EmailClient(
                account_type="pop3",
                server="x",
                username="u",
                password="p",
            )
            with pytest.raises(RepairableException) as exc_info:
                await client.connect()
        assert "Unsupported account type" in str(exc_info.value)
        assert "pop3" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connect_imap_failure_raises(self):
        from python.helpers.email_client import EmailClient
        from python.helpers.errors import RepairableException

        with patch("python.helpers.email_client.IMAPClient", side_effect=OSError("Connection refused")):
            with patch("python.helpers.email_client.PrintStyle"):
                client = EmailClient(
                    account_type="imap",
                    server="imap.gmail.com",
                    username="u",
                    password="p",
                )
                with pytest.raises(RepairableException) as exc_info:
                    await client.connect()
        assert "Email connection failed" in str(exc_info.value)


# --- EmailClient.disconnect ---


class TestEmailClientDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_imap_logout(self):
        from python.helpers.email_client import EmailClient

        mock_client = MagicMock()
        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        client.client = mock_client

        with patch("python.helpers.email_client.PrintStyle"):
            await client.disconnect()

        mock_client.logout.assert_called_once()
        assert client.client is None

    @pytest.mark.asyncio
    async def test_disconnect_exchange_clears_account(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(account_type="exchange", server="x", username="u", password="p")
        client.exchange_account = MagicMock()

        with patch("python.helpers.email_client.PrintStyle"):
            await client.disconnect()

        assert client.exchange_account is None

    @pytest.mark.asyncio
    async def test_disconnect_handles_logout_error(self):
        from python.helpers.email_client import EmailClient

        mock_client = MagicMock()
        mock_client.logout.side_effect = Exception("Logout failed")
        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        client.client = mock_client

        with patch("python.helpers.email_client.PrintStyle"):
            await client.disconnect()

        assert client.client is mock_client


# --- _decode_header ---


class TestDecodeHeader:
    def test_decode_header_empty(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        assert client._decode_header("") == ""

    def test_decode_header_plain_ascii(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        assert client._decode_header("Hello World") == "Hello World"

    def test_decode_header_encoded(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        # decode_header returns list of (bytes_or_str, encoding)
        with patch("python.helpers.email_client.decode_header") as mock_dh:
            mock_dh.return_value = [(b"Subject", "utf-8")]
            result = client._decode_header("=?utf-8?B?U3ViamVjdA==?=")
        assert result == "Subject"


# --- _html_to_text ---


class TestHtmlToText:
    def test_html_to_text_simple(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        result = client._html_to_text("<p>Hello <b>World</b></p>")
        assert "Hello" in result
        assert "World" in result

    def test_html_to_text_replaces_cid_with_file_marker(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        html = '<img src="cid:abc123" />'
        cid_map = {"abc123": "/a0/usr/email/image.png"}
        result = client._html_to_text(html, cid_map)
        assert "[file:///a0/usr/email/image.png]" in result

    def test_html_to_text_unknown_cid_unchanged(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        html = '<img src="cid:unknown" />'
        cid_map = {"known": "/path/to/file"}
        result = client._html_to_text(html, cid_map)
        assert "cid:unknown" in result or "unknown" in result


# --- _save_attachment_bytes ---


class TestSaveAttachmentBytes:
    @pytest.mark.asyncio
    async def test_save_attachment_returns_abs_path(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        with patch("python.helpers.email_client.files") as mock_files:
            mock_files.safe_file_name.return_value = "doc.pdf"
            mock_files.get_abs_path.return_value = "/a0/usr/email/doc_abc12345.pdf"
            path = await client._save_attachment_bytes("doc.pdf", b"content", "usr/email")
        assert path == "/a0/usr/email/doc_abc12345.pdf"
        mock_files.write_file_bin.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_attachment_sanitizes_filename(self):
        from python.helpers.email_client import EmailClient

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        with patch("python.helpers.email_client.files") as mock_files:
            mock_files.safe_file_name.return_value = "safe_name.pdf"
            mock_files.get_abs_path.return_value = "/a0/usr/email/safe_name_abc.pdf"
            await client._save_attachment_bytes("evil/name.pdf", b"x", "usr/email")
        mock_files.safe_file_name.assert_called_with("evil/name.pdf")


# --- _parse_message ---


class TestParseMessage:
    @pytest.mark.asyncio
    async def test_parse_single_part_plain(self):
        from python.helpers.email_client import EmailClient, Message

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        msg = StdEmailMessage()
        msg["From"] = "sender@example.com"
        msg["Subject"] = "Test Subject"
        msg.set_content("Plain body text")

        result = await client._parse_message(msg, "usr/email")
        assert isinstance(result, Message)
        assert result.sender == "sender@example.com"
        assert result.subject == "Test Subject"
        assert result.body.strip() == "Plain body text"
        assert result.attachments == []

    @pytest.mark.asyncio
    async def test_parse_multipart_with_attachment(self):
        from python.helpers.email_client import EmailClient, Message

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        mime_msg = MIMEMultipart()
        mime_msg["From"] = "a@b.com"
        mime_msg["Subject"] = "Multipart"
        mime_msg.attach(MIMEText("Body text", "plain"))
        part = MIMEBase("application", "octet-stream")
        part.set_payload(b"attachment content")
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename="file.bin")
        mime_msg.attach(part)

        with patch("python.helpers.email_client.files") as mock_files:
            mock_files.safe_file_name.return_value = "file.bin"
            mock_files.get_abs_path.return_value = "/a0/usr/email/file_abc.bin"
            result = await client._parse_message(mime_msg, "usr/email")

        assert "Body text" in result.body
        assert len(result.attachments) == 1
        assert result.attachments[0] == "/a0/usr/email/file_abc.bin"

    @pytest.mark.asyncio
    async def test_parse_html_fallback_when_no_plain(self):
        from python.helpers.email_client import EmailClient, Message

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        mime_msg = MIMEMultipart()
        mime_msg["From"] = "a@b.com"
        mime_msg["Subject"] = "HTML only"
        mime_msg.attach(MIMEText("<p>HTML body</p>", "html"))

        result = await client._parse_message(mime_msg, "usr/email")
        assert "HTML body" in result.body


# --- read_messages (IMAP flow) ---


class TestReadMessagesImap:
    @pytest.mark.asyncio
    async def test_read_messages_requires_connect_first(self):
        from python.helpers.email_client import EmailClient
        from python.helpers.errors import RepairableException

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        with patch("python.helpers.email_client.PrintStyle"):
            with pytest.raises(RepairableException) as exc_info:
                await client.read_messages("usr/email")
        assert "not connected" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_read_messages_imap_empty_inbox(self):
        from python.helpers.email_client import EmailClient

        mock_client = MagicMock()
        mock_client.select_folder.return_value = None
        mock_client.search.return_value = []

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        client.client = mock_client

        with patch("python.helpers.email_client.PrintStyle"):
            messages = await client.read_messages("usr/email")

        assert messages == []
        mock_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_messages_imap_with_filter(self):
        from python.helpers.email_client import EmailClient

        mock_client = MagicMock()
        mock_client.select_folder.return_value = None
        mock_client.search.return_value = [1]
        mock_client.fetch.return_value = {
            1: {
                b"RFC822": b"From: alice@example.com\r\nSubject: Hi\r\n\r\nHello",
            }
        }

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        client.client = mock_client

        with patch("python.helpers.email_client.PrintStyle"):
            messages = await client.read_messages(
                "usr/email",
                filter={"unread": True, "sender": "*@example.com", "subject": "*"},
            )

        assert len(messages) == 1
        assert messages[0].sender == "alice@example.com"
        assert messages[0].subject == "Hi"
        assert messages[0].body == "Hello"

    @pytest.mark.asyncio
    async def test_read_messages_sender_filter_excludes(self):
        from python.helpers.email_client import EmailClient

        mock_client = MagicMock()
        mock_client.select_folder.return_value = None
        mock_client.search.return_value = [1]
        mock_client.fetch.return_value = {
            1: {
                b"RFC822": b"From: bob@other.com\r\nSubject: Hi\r\n\r\nHello",
            }
        }

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        client.client = mock_client

        with patch("python.helpers.email_client.PrintStyle"):
            messages = await client.read_messages(
                "usr/email",
                filter={"sender": "*@example.com"},
            )

        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_read_messages_subject_filter_excludes(self):
        from python.helpers.email_client import EmailClient

        mock_client = MagicMock()
        mock_client.select_folder.return_value = None
        mock_client.search.return_value = [1]
        mock_client.search.return_value = [1]
        mock_client.fetch.return_value = {
            1: {
                b"RFC822": b"From: alice@example.com\r\nSubject: Spam\r\n\r\nHi",
            }
        }

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        client.client = mock_client

        with patch("python.helpers.email_client.PrintStyle"):
            messages = await client.read_messages(
                "usr/email",
                filter={"subject": "*invoice*"},
            )

        assert len(messages) == 0


# --- read_messages convenience function ---


class TestReadMessagesConvenience:
    @pytest.mark.asyncio
    async def test_read_messages_connects_and_disconnects(self):
        from python.helpers.email_client import read_messages

        with patch("python.helpers.email_client.EmailClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_instance.disconnect = AsyncMock()
            mock_instance.read_messages = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            await read_messages(
                server="imap.gmail.com",
                username="u",
                password="p",
                download_folder="usr/email",
            )

            mock_instance.connect.assert_awaited_once()
            mock_instance.disconnect.assert_awaited_once()
            mock_instance.read_messages.assert_awaited_once_with("usr/email", None)


# --- Error handling and edge cases ---


class TestEmailClientEdgeCases:
    @pytest.mark.asyncio
    async def test_fetch_handles_line_too_long_retry(self):
        from python.helpers.email_client import EmailClient

        mock_client = MagicMock()
        mock_client.select_folder.return_value = None
        mock_client.search.return_value = [1]
        mock_client.fetch.side_effect = [
            Exception("line too long"),
            {1: {b"BODY[]": b"From: a@b.com\r\nSubject: S\r\n\r\nB"}},
        ]

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        client.client = mock_client

        with patch("python.helpers.email_client.PrintStyle"):
            messages = await client.read_messages("usr/email")

        assert len(messages) == 1
        assert messages[0].body == "B"

    @pytest.mark.asyncio
    async def test_skips_message_on_unexpected_response_format(self):
        from python.helpers.email_client import EmailClient

        mock_client = MagicMock()
        mock_client.select_folder.return_value = None
        mock_client.search.return_value = [1, 2]
        # First message has no RFC822/BODY[] key -> returns None; second succeeds
        mock_client.fetch.side_effect = [
            {1: {}},  # Unexpected format
            {2: {b"RFC822": b"From: a@b.com\r\nSubject: OK\r\n\r\nBody"}},
        ]

        client = EmailClient(account_type="imap", server="x", username="u", password="p")
        client.client = mock_client

        with patch("python.helpers.email_client.PrintStyle"):
            messages = await client.read_messages("usr/email")

        assert len(messages) == 1
        assert messages[0].subject == "OK"

    @pytest.mark.asyncio
    async def test_exchange_requires_connect_first(self):
        from python.helpers.email_client import EmailClient
        from python.helpers.errors import RepairableException

        client = EmailClient(account_type="exchange", server="x", username="u", password="p")
        with patch("python.helpers.email_client.PrintStyle"):
            with pytest.raises(RepairableException) as exc_info:
                await client.read_messages("usr/email")
        assert "not connected" in str(exc_info.value).lower()
