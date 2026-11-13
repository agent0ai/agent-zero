from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path

import psutil
from filelock import FileLock, Timeout

from helpers import files, plugins
from helpers.localization import Localization
from helpers.notification import NotificationManager, NotificationPriority, NotificationType
from helpers.task_scheduler import TaskScheduler, ScheduledTask, TaskSchedule, TaskState, serialize_task
from plugins._a0_cleaner.helpers.cleaner import Cleaner, CleanerError, atomic_json, read_json

NAME = '_a0_cleaner'
TASK_ID = 'a0-cleaner-maintenance'
CADENCES = {'daily': ('0', '9', '*', '*', '*'), 'weekly': ('0', '9', '*', '*', '1'), 'monthly': ('0', '9', '1', '*', '*')}


def state_dir():
    return Path(files.get_abs_path('usr/plugin_data', NAME))


def process_inventory():
    paths = set()
    package_busy = False
    opaque_uids = set()
    for process in psutil.process_iter():
        try:
            args = process.cmdline()
            try:
                paths.update(item.path for item in process.open_files())
                cwd = process.cwd()
                if cwd:
                    paths.add(cwd)
            except psutil.AccessDenied:
                uid = process.uids().effective
                if uid in (0, os.geteuid()):
                    raise
                opaque_uids.add(uid)
            for arg in args:
                value = arg.partition('=')[2] if '=' in arg else arg
                if value.startswith('/'):
                    paths.add(value)
                if Path(arg).name in ('pip', 'pip3', 'uv', 'npm', 'npm-cli.js', 'npx', 'apt', 'apt-get', 'dpkg'):
                    package_busy = True
            if '-m' in args and 'pip' in args:
                package_busy = True
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
        except psutil.AccessDenied as exc:
            raise CleanerError('Running processes could not be checked. Cleanup is paused.') from exc
    return {'paths': sorted(paths), 'package_busy': package_busy, 'opaque_uids': sorted(opaque_uids),
            'mounts': [partition.mountpoint for partition in psutil.disk_partitions(all=True)]}


def chat_activity(chat_id):
    from agent import AgentContext

    context = AgentContext.get(chat_id)
    if context:
        if context.is_running() or context.paused:
            return float('inf')
        return context.last_message.timestamp() if context.last_message else None
    try:
        data = json.loads(Path(files.get_abs_path('usr/chats', chat_id, 'chat.json')).read_text())
        stamp = datetime.fromisoformat(data['last_message'])
        if stamp.tzinfo is None:
            stamp = Localization.get().localize_naive_datetime(stamp)
        return stamp.timestamp()
    except (OSError, ValueError, KeyError, TypeError):
        return None


def service(cancel_event=None, config=None):
    from plugins._browser.helpers.playwright import get_playwright_chromium_revision

    return Cleaner(files.get_base_dir(), Path.home(), state_dir(),
                   config=plugins.get_plugin_config(NAME) if config is None else config,
                   process_inventory=process_inventory, chat_activity=chat_activity,
                   enabled=lambda: plugins.get_toggle_state(NAME) == 'enabled', cancel_event=cancel_event,
                   browser_revision=get_playwright_chromium_revision())


async def ensure_task(*, recreate=False):
    state_dir().mkdir(parents=True, exist_ok=True)
    try:
        with FileLock(str(state_dir()/'schedule.lock'), timeout=0):
            return await _ensure_task(recreate=recreate)
    except Timeout as exc:
        raise CleanerError('The cleaner schedule is being updated. Try again shortly.') from exc


async def _ensure_task(*, recreate=False):
    scheduler = TaskScheduler.get()
    await scheduler.reload()
    task = scheduler.get_task_by_uuid(TASK_ID)
    if task:
        if task.plugin_name != NAME:
            raise CleanerError('The cleaner schedule ID is already in use.')
        return task
    marker = state_dir()/'schedule-installed.json'
    if marker.exists() and not recreate:
        return None
    task = ScheduledTask(
        uuid=TASK_ID, name='A0Cleaner', plugin_name=NAME, system_prompt='',
        prompt='Scan storage, clean the enabled areas, and report files awaiting review.',
        schedule=TaskSchedule(minute='0', hour='9', day='*', month='*', weekday='1',
                              timezone=Localization.get().get_timezone()),
    )
    await scheduler.add_task(task)
    atomic_json(marker, {'task_id': TASK_ID})
    return task


async def schedule_info():
    task = await ensure_task()
    if task is None:
        return {'cadence': 'off', 'task': None}
    cadence = next((key for key, fields in CADENCES.items() if task.schedule.to_crontab() == ' '.join(fields)), 'custom')
    if task.state == TaskState.DISABLED:
        cadence = 'off'
    return {'cadence': cadence, 'task': serialize_task(task)}


async def set_schedule(cadence):
    if cadence not in (*CADENCES, 'off'):
        raise CleanerError('Choose daily, weekly, monthly or off.')
    task = await ensure_task(recreate=True)
    scheduler = TaskScheduler.get()
    if task.state == TaskState.RUNNING:
        raise CleanerError('Wait for the current maintenance run to finish.')
    if cadence == 'off':
        await scheduler.update_task(TASK_ID, state=TaskState.DISABLED)
    else:
        fields = CADENCES[cadence]
        schedule = TaskSchedule(**dict(zip(('minute','hour','day','month','weekday'), fields)), timezone=task.schedule.timezone)
        await scheduler.update_task(TASK_ID, schedule=schedule, state=TaskState.IDLE)
    return await schedule_info()


def format_bytes(size):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024 or unit == 'TB':
            return f'{size:.1f} {unit}' if unit != 'B' else f'{size} B'
        size /= 1024


def notify(summary):
    found, freed = summary['found_bytes'], summary['freed_bytes']
    if not found and not freed:
        return
    action = (f'<div class="toast-action-row"><button type="button" class="button confirm" '
              f'@click.stop="ensureModalOpen(\'/plugins/{NAME}/webui/main.html\')">Clean up</button></div>') if found else ''
    NotificationManager.send_notification(
        type=NotificationType.INFO if found else NotificationType.SUCCESS,
        priority=NotificationPriority.NORMAL, title=f'A0 found {format_bytes(found)} of unused files' if found else f'A0 cleaned {format_bytes(freed)}',
        message=(f'{format_bytes(freed)} cleaned automatically.' if freed else '') + action,
        display_time=0 if found else 6, group='a0_cleaner', id='a0_cleaner_scan',
    )


def run_scheduled(cancel_event=None):
    summary = service(cancel_event).scheduled()
    notify(summary)
    return f"Cleaned {format_bytes(summary['freed_bytes'])}. {format_bytes(summary['found_bytes'])} available for review."


def save_settings(settings):
    cleaner = service(config=settings)
    cleaner.areas(validate_custom=True)
    with cleaner.operation('Saving settings'):
        plugins.save_plugin_config(NAME, '', '', cleaner.config)
    return cleaner.config
