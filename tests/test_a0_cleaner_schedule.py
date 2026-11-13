import asyncio
from types import SimpleNamespace

import psutil
import pytest

from helpers import task_scheduler as scheduler
from plugins._a0_cleaner.helpers import runtime as cleaner_runtime
from test_task_scheduler_recovery import runtime


def test_schedule_registration_is_idempotent_and_respects_user_edits_and_deletion(runtime, monkeypatch, tmp_path):
    monkeypatch.setattr(cleaner_runtime, 'state_dir', lambda:tmp_path/'cleaner')
    first=asyncio.run(cleaner_runtime.ensure_task())
    second=asyncio.run(cleaner_runtime.ensure_task())
    assert first.uuid==second.uuid and first.plugin_name=='_a0_cleaner'
    assert len(runtime.engine.get_tasks())==1
    assert first.schedule.to_crontab()=='0 9 * * 1'
    changed=scheduler.TaskSchedule(minute='30',hour='17',day='*',month='*',weekday='4',timezone='Europe/Rome')
    asyncio.run(runtime.engine.update_task(first.uuid,schedule=changed,state=scheduler.TaskState.DISABLED))
    persisted=asyncio.run(cleaner_runtime.ensure_task())
    assert persisted.schedule==changed and persisted.state==scheduler.TaskState.DISABLED
    asyncio.run(runtime.engine.remove_task_by_uuid(first.uuid))
    assert asyncio.run(cleaner_runtime.ensure_task()) is None
    assert not runtime.engine.get_tasks()
    info=asyncio.run(cleaner_runtime.set_schedule('daily'))
    assert info['cadence']=='daily' and len(runtime.engine.get_tasks())==1


def test_notification_opens_review_instead_of_deleting(monkeypatch):
    calls=[]
    monkeypatch.setattr(cleaner_runtime.NotificationManager,'send_notification',lambda **kwargs:calls.append(kwargs))
    cleaner_runtime.notify({'found_bytes':1024**3,'freed_bytes':1024**2})
    assert len(calls)==1
    assert 'A0 found 1.0 GB' in calls[0]['title']
    assert 'Clean up' in calls[0]['message']
    assert '/plugins/_a0_cleaner/webui/main.html' in calls[0]['message']
    assert 'confirmed' not in calls[0]['message']


@pytest.mark.parametrize('uid,raises',[(99999,False),(0,True)])
def test_process_visibility_is_scoped_to_the_affected_owner(monkeypatch,uid,raises):
    class Process:
        def cmdline(self): return ['python','/opt/service/webapp.py']
        def open_files(self): raise psutil.AccessDenied(16)
        def uids(self): return SimpleNamespace(effective=uid)
    monkeypatch.setattr(cleaner_runtime.psutil,'process_iter',lambda:[Process()])
    monkeypatch.setattr(cleaner_runtime.psutil,'disk_partitions',lambda **kwargs:[])
    if raises:
        with pytest.raises(cleaner_runtime.CleanerError,match='paused'):
            cleaner_runtime.process_inventory()
    else:
        result=cleaner_runtime.process_inventory()
        assert result['opaque_uids']==[uid]
        assert not result['package_busy']
