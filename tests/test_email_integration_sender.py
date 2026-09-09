import asyncio
import smtplib
from unittest.mock import AsyncMock, MagicMock, patch

from plugins._email_integration.helpers import imap_client, smtp_client


def test_imap_sender_validation_and_reply_recipient():
    send_message = smtplib.SMTP.send_message
    cases = [
        ([], None),
        ([""], None),
        (["not an address"], None),
        (["boss@company.com", "attacker@evil.example"], None),
        (["attacker@evil.example, boss@company.com"], None),
        (["boss@company.com, attacker@evil.example"], None),
        (["Boss <boss@company.com>, attacker@evil.example"], None),
        (["Staff: boss@company.com;"], None),
        (["Boss <boss@company.com"], None),
        (["boss@company.com"], "boss@company.com"),
        (["Boss <Boss@Company.com>"], "Boss@Company.com"),
        (["=?utf-8?q?B=C3=B6ss?= <boss@company.com>"], "boss@company.com"),
        (["Boss\r\n <boss@company.com>"], "boss@company.com"),
        (["attacker@evil.example"], "attacker@evil.example"),
        (['"boss@company.com" <attacker@evil.example>'], "attacker@evil.example"),
        (["no-reply@company.com"], None),
    ]
    for from_headers, address in cases:
        raw = (
            "".join(f"From: {value}\r\n" for value in from_headers)
            + "Subject: sender test\r\n\r\nHarmless test body."
        ).encode()
        for whitelist in (None, ["*@company.com"], ["boss@company.com"]):
            accepted = address is not None and (
                whitelist is None or address.lower() == "boss@company.com"
            )
            for fetch in (imap_client.fetch_new, imap_client.fetch_unread_since):
                client = MagicMock()
                client.gmail_search.return_value = [42]
                client.fetch.return_value = {42: {b"RFC822": raw}}
                with patch.object(imap_client, "_parse_body", new_callable=AsyncMock) as body:
                    body.return_value = ("Harmless test body.", [])
                    messages, uid = asyncio.run(fetch(client, "unused", 1, whitelist))
                assert uid == 42
                assert bool(messages) == accepted, (from_headers, whitelist, fetch.__name__)
                assert body.await_count == int(accepted)
                client.add_flags.assert_called_once_with([42], [b"\\Seen"])
                if accepted:
                    assert messages[0].sender == address

                    # Keep real SMTP recipient derivation; intercept transport only.
                    with patch.object(smtp_client.smtplib, "SMTP") as smtp:
                        server = smtp.return_value.__enter__.return_value
                        server.send_message.side_effect = lambda msg: send_message(server, msg)
                        server.ehlo_or_helo_if_needed.return_value = None
                        error = asyncio.run(smtp_client.send_reply(
                            smtp_client.SmtpConfig("unused", username="agent@example.org"),
                            to=messages[0].sender,
                            subject="Re: sender test",
                            body="Harmless reply.",
                        ))
                    assert error is None
                    assert server.sendmail.call_args.args[1] == [address]
