"""Mail transports; credentials are request input, never logs or installed state."""
import asyncio
import base64
from dataclasses import asdict
import sys
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, '/plugin/sandbox')
import imap_client
import smtp_client

clients = {}
loop = asyncio.new_event_loop()


async def dispatch(payload):
    action = payload['action']
    if action in ('connect_imap', 'connect_exchange'):
        client = await getattr(imap_client, action)(**payload['kwargs'])
        handle = uuid.uuid4().hex
        clients[handle] = client
        return handle
    if action in ('test_smtp', 'send_reply'):
        config = smtp_client.SmtpConfig(**payload['config'])
        kwargs = payload.get('kwargs', {})
        if kwargs.get('attachments'):
            kwargs['attachments'] = [(name, base64.b64decode(data, validate=True))
                                     for name, data in kwargs['attachments']]
        return await getattr(smtp_client, action)(config, **kwargs)
    client = clients[payload['handle']]
    if action == 'disconnect_imap':
        clients.pop(payload['handle'])
        return await imap_client.disconnect_imap(client)
    if action == 'exchange_count':
        try:
            return await asyncio.to_thread(lambda: client.inbox.total_count)
        finally:
            clients.pop(payload['handle'], None)
            await asyncio.to_thread(client.protocol.close)
    if action == 'get_highest_uid':
        return await imap_client.get_highest_uid(client)
    if action not in ('fetch_new', 'fetch_unread_since', 'fetch_unread_exchange'):
        raise ValueError('Unsupported mail worker action')
    try:
        with TemporaryDirectory() as folder:
            result = await getattr(imap_client, action)(client, folder, **payload['kwargs'])
            def serialize(message):
                value = asdict(message)
                value['attachments'] = []
                for filename in message.attachments:
                    path = Path(filename)
                    value['attachments'].append({'name': path.name, 'data': base64.b64encode(path.read_bytes()).decode()})
                    value['body'] = value['body'].replace(filename, path.name)
                return value
            if action == 'fetch_unread_exchange':
                return [serialize(message) for message in result]
            messages, uid = result
            return [serialize(message) for message in messages], uid
    finally:
        if action == 'fetch_unread_exchange':
            clients.pop(payload['handle'], None)
            await asyncio.to_thread(client.protocol.close)


def handle(payload):
    try:
        return loop.run_until_complete(dispatch(payload))
    except Exception as exc:
        # Transport exceptions can contain credentials, addresses or server replies.
        raise RuntimeError(f'Mail transport failed ({type(exc).__name__})') from None
