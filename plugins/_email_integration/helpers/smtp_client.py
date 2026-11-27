"""SMTP control client; only selected attachments cross as bytes."""
import base64
from dataclasses import dataclass, asdict
from plugins._email_integration.helpers.sandbox import call


@dataclass
class SmtpConfig:
    server: str
    port: int = 587
    username: str = ''
    password: str = ''
    use_tls: bool = True


async def send_reply(config, to, subject, body, in_reply_to='', references='', attachments=None):
    return await call({'action': 'send_reply', 'config': asdict(config), 'kwargs': dict(
        to=to, subject=subject, body=body, in_reply_to=in_reply_to, references=references,
        attachments=[(name, base64.b64encode(data).decode()) for name, data in attachments] if attachments else None)})


async def test_smtp(config):
    return await call({'action': 'test_smtp', 'config': asdict(config)})
