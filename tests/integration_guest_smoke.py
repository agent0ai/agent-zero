"""Run inside a provisioned integration guest: python - <this file, with no live accounts."""
import asyncio
import base64
from email.message import EmailMessage
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, '/plugin/sandbox')
import worker


def telegram():
    from aiogram import Bot
    from aiogram.types import User, Message
    calls = []
    async def transport(bot, method, **kwargs):
        calls.append(method)
        name = type(method).__name__
        if name == 'GetMe':
            return User(id=123456, is_bot=True, first_name='Fixture', username='fixture_bot')
        if name.startswith('Send'):
            if name == 'SendDocument':
                assert method.document.data == b'fixture file'
            return Message.model_validate({'message_id': 7, 'date': 1700000000,
                                           'chat': {'id': 42, 'type': 'private'}})
        return True
    token = '123456:fixture'
    with patch.object(Bot, '__call__', transport):
        created = worker.handle({'action':'create', 'name':'fixture', 'token':token,
                                 'commands':['status'], 'group_mode':'off'})
        assert created['username'] == 'fixture_bot', created
        event = {'update_id':1, 'message':{'message_id':1, 'date':1700000000, 'text':'/status',
                 'from':{'id':42, 'is_bot':False, 'first_name':'Fixture'},
                 'chat':{'id':42,'type':'private'},
                 'entities':[{'type':'bot_command','offset':0,'length':7}]}}
        events = worker.handle({'action':'webhook','name':'fixture','update':event})
        assert events[0]['kind'] == 'control' and events[0]['event']['text'] == '/status', events
        event['message']['chat']['type'] = 'group'
        assert worker.handle({'action':'webhook','name':'fixture','update':event}) == []
        for method, kwargs in [('send_message',{'text':'fixture'}), ('send_document',{
            'document':{'file_name':'fixture.txt','file_data':base64.b64encode(b'fixture file').decode()}})]:
            result = worker.handle({'action':'method','method':method,'token':token,'kwargs':{'chat_id':42,**kwargs}})
            assert result['message_id'] == 7, result
        assert worker.handle({'action':'stop','name':'fixture'}) is True
        assert not worker.bot_manager.get_all_bots()
    print('Telegram real SDK webhook routing, group rejection, outgoing bytes and shutdown passed; network mocked')


def mail():
    raw = EmailMessage()
    raw['From']='fixture@example.invalid';raw['To']='a0@example.invalid';raw['Subject']='Fixture'
    raw['Message-ID']='<fixture@example.invalid>'
    raw.set_content('Fixture inbound body')
    raw.add_attachment(b'fixture attachment',maintype='application',subtype='octet-stream',filename='fixture.txt')
    sent=[]
    class IMAP:
        _imap=SimpleNamespace()
        def __init__(self,*a,**kw): pass
        def login(self,*a): pass
        def logout(self): pass
        def select_folder(self,*a): pass
        def search(self,*a): return [7]
        def gmail_search(self,*a): return [7]
        def fetch(self,*a): return {7:{b'RFC822':raw.as_bytes()}}
        def add_flags(self,*a): pass
    class SMTP:
        def __init__(self,*a,**kw): pass
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def login(self,*a): pass
        def send_message(self,message): sent.append(message)
    with patch.object(worker.imap_client,'IMAPClient',IMAP), patch.object(worker.smtp_client.smtplib,'SMTP_SSL',SMTP):
        handle = worker.handle({'action':'connect_imap','kwargs':{'server':'fixture.invalid'}})
        messages, uid = worker.handle({'action':'fetch_new','handle':handle,'kwargs':{'last_uid':6,'sender_whitelist':['fixture@example.invalid']}})
        assert uid == 7 and len(messages)==1, messages
        assert base64.b64decode(messages[0]['attachments'][0]['data'])==b'fixture attachment'
        assert worker.handle({'action':'fetch_new','handle':handle,'kwargs':{'last_uid':7}})==([],7)
        worker.handle({'action':'disconnect_imap','handle':handle}); assert not worker.clients
        assert worker.handle({'action':'send_reply','config':{'server':'fixture.invalid','use_tls':False,'username':'a0@example.invalid'},
            'kwargs':{'to':'fixture@example.invalid','subject':'Reply','body':'Fixture reply','in_reply_to':'<fixture@example.invalid>',
                      'attachments':[['fixture.txt',base64.b64encode(b'outbound').decode()]]}}) is None
        assert sent[0]['In-Reply-To']=='<fixture@example.invalid>'
        assert any(part.get_payload(decode=True)==b'outbound' for part in sent[0].walk())
    print('Mail real MIME/parser attachment, UID reuse, SMTP threading and cleanup passed; network mocked')


if __name__ == '__main__':
    if hasattr(worker,'bot_manager'): telegram()
    else: mail()
