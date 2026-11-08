"""Mail control client. Transport libraries and parsing execute in the guest."""
from dataclasses import dataclass, field
from pathlib import Path
import base64
import os
import re
import uuid
from helpers import files
from plugins._email_integration.helpers.sandbox import call


@dataclass
class InboundMessage:
    sender: str
    subject: str
    body: str
    attachments: list[str] = field(default_factory=list)
    message_id: str = ''
    in_reply_to: str = ''
    references: str = ''


def _messages(values):
    messages = []
    for value in values:
        paths = []
        for attachment in value['attachments']:
            name = attachment['name']
            if not isinstance(name, str) or not name or Path(name).name != name or name in ('.', '..'):
                raise ValueError('Invalid mail attachment path')
            data = base64.b64decode(attachment['data'], validate=True)
            safe_name = re.sub(r'[^a-zA-Z0-9-._]', '_', name)
            path = Path(files.get_abs_path('usr/email/attachments', uuid.uuid4().hex + '-' + safe_name))
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as stream:
                stream.write(data)
            paths.append(str(path))
            value['body'] = value['body'].replace('attachment://' + name, 'attachment://' + str(path))
        value['attachments'] = paths
        messages.append(InboundMessage(**value))
    return messages


async def connect_imap(server, port=993, username='', password='', ssl=True, timeout=30):
    return await call({'action': 'connect_imap', 'kwargs': dict(server=server, port=port,
                       username=username, password=password, ssl=ssl, timeout=timeout)})


async def disconnect_imap(client):
    from plugins._email_integration.helpers.sandbox import worker
    if worker.ready:
        try:
            await call({'action': 'disconnect_imap', 'handle': client})
        except Exception:
            # Cleanup failure must not suppress a successful poll's UID checkpoint.
            pass


async def get_highest_uid(client):
    return await call({'action': 'get_highest_uid', 'handle': client})


async def fetch_new(client, download_folder, last_uid=0, sender_whitelist=None, max_messages=10):
    messages, uid = await call({'action': 'fetch_new', 'handle': client, 'kwargs': dict(
        last_uid=last_uid, sender_whitelist=sender_whitelist, max_messages=max_messages)})
    return _messages(messages), uid


async def fetch_unread_since(client, download_folder, days, sender_whitelist=None, max_messages=10):
    messages, uid = await call({'action': 'fetch_unread_since', 'handle': client, 'kwargs': dict(
        days=days, sender_whitelist=sender_whitelist, max_messages=max_messages)})
    return _messages(messages), uid


async def connect_exchange(server, username, password):
    return await call({'action': 'connect_exchange', 'kwargs': dict(
        server=server, username=username, password=password)})


async def exchange_count(account):
    return await call({'action': 'exchange_count', 'handle': account})


async def fetch_unread_exchange(account, download_folder, sender_whitelist=None, since_days=0):
    return _messages(await call({'action': 'fetch_unread_exchange', 'handle': account, 'kwargs': dict(
        sender_whitelist=sender_whitelist, since_days=since_days)}))
