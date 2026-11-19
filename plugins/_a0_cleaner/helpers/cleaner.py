"""Inventory and identity-checked cleanup of known disposable container files."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time
import uuid

from filelock import FileLock, Timeout


DAY = 86400
PROTECTED_NAMES = {'.git', '.a0proj', '.time_travel', '.env', 'repo.git'}
AUTO_AREAS = {'pip', 'npm', 'staging', 'profiles', 'screenshots', 'captures', 'browser_versions'}
DEFAULTS = {'automatic': True, 'automatic_areas': sorted(AUTO_AREAS), 'cache_days': 30,
            'staging_days': 7, 'review_days': 30, 'custom_folders': []}


class CleanerError(ValueError):
    pass


def config_values(values=None):
    result = {**DEFAULTS, **(values or {})}
    if not isinstance(result['automatic'], bool):
        raise CleanerError('Automatic cleanup must be on or off.')
    if not isinstance(result['automatic_areas'], list) or any(not isinstance(item, str) or item not in AUTO_AREAS for item in result['automatic_areas']):
        raise CleanerError('Choose supported areas for automatic cleanup.')
    result['automatic_areas'] = sorted(set(result['automatic_areas']))
    for key in ('cache_days', 'staging_days', 'review_days'):
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 3650:
            raise CleanerError('File age must be between 1 and 3650 days.')
    folders = result['custom_folders']
    if not isinstance(folders, list) or len(folders) > 20:
        raise CleanerError('Choose up to 20 custom folders.')
    return result


def fingerprint(info):
    return [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]


def allocated(info):
    return info.st_blocks * 512


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False, encoding='utf-8') as handle:
        temporary = handle.name
        json.dump(value, handle)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def read_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default


@contextmanager
def directory_fd(path: Path):
    """Walk from / with O_NOFOLLOW, including every ancestor of a deletion target."""
    path = Path(os.path.abspath(path))
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield fd
    finally:
        os.close(fd)


@dataclass
class Area:
    id: str
    title: str
    icon: str
    automatic: bool
    days: int
    roots: list[Path]
    impact: str
    kind: str = 'files'


class Cleaner:
    def __init__(self, base, home, state, *, config=None, process_inventory=None, chat_activity=None,
                 enabled=lambda: True, clock=time.time, cancel_event=None, browser_revision=''):
        self.base, self.home, self.state = Path(base), Path(home), Path(state)
        self.config = config_values(config)
        self.process_inventory = process_inventory or (lambda: {'paths': [], 'package_busy': False})
        self.chat_activity = chat_activity or (lambda chat: None)
        self.enabled, self.clock, self.cancel_event = enabled, clock, cancel_event
        self._last_enabled_check = float('-inf')
        self.browser_revision = str(browser_revision)
        self._mounts = set()
        self.state.mkdir(parents=True, exist_ok=True)
        self.lock = FileLock(str(self.state / 'operation.lock'), timeout=0, is_singleton=True)

    def custom_path(self, raw, *, allow_missing=False):
        if not isinstance(raw, str) or not raw.strip() or '\0' in raw or not Path(raw).is_absolute():
            raise CleanerError('Choose an absolute folder path.')
        path = Path(os.path.abspath(raw))
        if any(part in PROTECTED_NAMES or part.startswith('.env.') for part in path.parts):
            raise CleanerError('That folder contains protected configuration or history.')
        permitted = [self.base/'usr/workdir', self.base/'usr/downloads', self.base/'usr/uploads', self.base/'tmp']
        allowed = any(path.is_relative_to(root) and path != root for root in permitted)
        projects = self.base/'usr/projects'
        allowed = allowed or (path.is_relative_to(projects) and len(path.relative_to(projects).parts) >= 2)
        if not allowed:
            raise CleanerError('Choose a subfolder of workdir, a project, downloads, uploads or A0 tmp.')
        managed = [self.base/'tmp/browser', self.base/'tmp/desktop', self.base/'tmp/playwright',
                   self.base/'tmp/memory', self.state]
        managed += [root for area in self.areas(include_custom=False) for root in area.roots]
        if any(path.is_relative_to(root) or root.is_relative_to(path) for root in managed):
            raise CleanerError('Use the dedicated cleanup area for that folder.')
        try:
            checked = path
            if allow_missing:
                while not checked.exists() and not checked.is_symlink():
                    checked = checked.parent
            with directory_fd(checked):
                pass
        except OSError as exc:
            raise CleanerError('Choose an existing folder without symbolic links.') from exc
        return path

    def areas(self, include_custom=True, *, validate_custom=False):
        cfg = self.config
        areas = [
            Area('pip', 'Python download cache', 'deployed_code', True, cfg['cache_days'],
                 [self.home/'.cache/pip'], 'Packages may need to be downloaded again.'),
            Area('npm', 'Node download cache', 'deployed_code', True, cfg['cache_days'],
                 [self.home/'.npm/_cacache', self.home/'.npm/_logs'], 'Packages may need to be downloaded again.'),
            Area('staging', 'Installer leftovers', 'inventory_2', True, cfg['staging_days'],
                 [self.base/'tmp'/name for name in ('plugin_uploads', 'plugin_installs', 'plugins_installer', 'skill_imports')],
                 'Removes old temporary installation files.'),
            Area('profiles', 'Retired browser profiles', 'web', False, cfg['review_days'],
                 [self.base/'tmp/browser/sessions'], 'Saved sign-ins and tabs in these retired profiles will be removed.', 'profiles'),
            Area('screenshots', 'Old chat screenshots', 'photo_library', False, cfg['review_days'],
                 [self.base/'usr/chats'], 'Old screenshot previews will no longer open. Chat text and uploaded images remain.', 'screenshots'),
            Area('captures', 'Temporary captures', 'screenshot_monitor', False, cfg['review_days'],
                 [self.base/'tmp/browser/screenshots', self.base/'tmp/desktop/screenshots'],
                 'Old links to these temporary captures will no longer open.'),
            Area('embeddings', 'Embedding cache', 'memory', False, cfg['review_days'],
                 [self.base/'tmp/memory/embeddings'], 'Embeddings are rebuilt when needed; remote models may incur usage.'),
            Area('browser_versions', 'Unused browser versions', 'download_done', False, cfg['review_days'],
                 [self.base/'tmp/playwright'], 'Older browser installations will be removed. Other tools may download them again.', 'versions'),
        ]
        for area in areas:
            area.automatic = area.id in cfg['automatic_areas']
        if include_custom:
            seen = []
            for index, folder in enumerate(cfg['custom_folders']):
                if not isinstance(folder, dict) or not isinstance(folder.get('days'), int) or isinstance(folder['days'], bool) or not 0 <= folder['days'] <= 3650:
                    raise CleanerError('Each custom folder needs a path and a valid file age.')
                path = self.custom_path(folder.get('path'), allow_missing=not validate_custom)
                if any(path.is_relative_to(other) or other.is_relative_to(path) for other in seen):
                    raise CleanerError('Custom folders must not overlap.')
                seen.append(path)
                areas.append(Area(f'custom-{index}', path.name, 'folder', False, folder['days'], [path],
                                  (f'Files older than {folder["days"]} days in this folder will be permanently removed.'
                                   if folder['days'] else 'All eligible files in this folder will be permanently removed.'), 'custom'))
        return areas

    def _check(self):
        if self.cancel_event and self.cancel_event.is_set():
            raise CleanerError('Cleanup stopped.')
        if time.monotonic() - self._last_enabled_check >= .2:
            if not self.enabled():
                raise CleanerError('A0Cleaner is disabled.')
            self._last_enabled_check = time.monotonic()

    def _walk(self, root, budget):
        if not root.exists() and not root.is_symlink():
            return
        with directory_fd(root) as fd:
            device = os.fstat(fd).st_dev
        stack = [root]
        while stack:
            self._check()
            if time.monotonic() > budget['deadline'] or budget['files'] > 250000:
                raise CleanerError('Scan limit reached. Select a smaller custom folder and scan again.')
            folder = stack.pop()
            with directory_fd(folder) as fd, os.scandir(fd) as entries:
                for entry in entries:
                    budget['files'] += 1
                    if budget['files'] > 250000 or (budget['files'] % 256 == 0 and time.monotonic() > budget['deadline']):
                        raise CleanerError('Scan limit reached. Select a smaller custom folder and scan again.')
                    if entry.name in PROTECTED_NAMES or entry.name.startswith('.env.'):
                        continue
                    info = entry.stat(follow_symlinks=False)
                    if info.st_dev != device or stat.S_ISLNK(info.st_mode):
                        continue
                    path = folder/entry.name
                    if str(path) in self._mounts:
                        continue
                    if stat.S_ISDIR(info.st_mode):
                        stack.append(path)
                    elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                        yield path, info

    @staticmethod
    def _in_use(root, inventory):
        return any(Path(path).is_relative_to(root) for path in inventory['paths'])

    def _roots(self, area, cutoff, inventory):
        if area.id in ('pip', 'npm', 'staging') and inventory['package_busy']:
            return
        for root in area.roots:
            if area.kind not in ('profiles', 'screenshots', 'versions'):
                if not self._in_use(root, inventory):
                    yield root, ''
                continue
            if not root.exists():
                continue
            with directory_fd(root) as fd, os.scandir(fd) as entries:
                for entry in entries:
                    if not entry.is_dir(follow_symlinks=False) or entry.is_symlink():
                        continue
                    child = root/entry.name
                    if area.kind == 'versions':
                        if not self.browser_revision or not entry.name.startswith(('chromium-', 'chromium_headless_shell-')):
                            continue
                        revision = entry.name.rsplit('-', 1)[-1]
                        if not revision.isdigit() or revision == self.browser_revision or self._in_use(child, inventory):
                            continue
                        yield child, ''
                        continue
                    if area.kind == 'profiles':
                        if entry.name in ('shared', 'default', '__shared__') or self._in_use(child, inventory):
                            continue
                        yield child, ''
                    else:
                        activity = self.chat_activity(entry.name)
                        if activity is not None and activity < cutoff:
                            yield child/'screenshots', entry.name

    def _scan(self):
        self._check()
        now = self.clock()
        inventory = self.process_inventory()
        self._mounts = set(inventory.get('mounts', []))
        budget = {'files': 0, 'deadline': time.monotonic() + 90}
        groups, candidates = [], []
        for area in self.areas():
            items = []
            errors = []
            cutoff = now - area.days*DAY
            try:
                for root, chat in self._roots(area, cutoff, inventory):
                    contents = list(self._walk(root, budget))
                    # Retired profiles are one unit: a recent file protects the entire profile.
                    if area.kind in ('profiles', 'versions') and any(max(s.st_mtime, s.st_ctime) >= cutoff for _, s in contents):
                        continue
                    for path, info in contents:
                        if max(info.st_mtime, info.st_ctime) >= cutoff or str(path) in inventory['paths']:
                            continue
                        if info.st_uid in inventory.get('opaque_uids', []):
                            continue
                        if area.id in ('screenshots', 'captures') and path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'):
                            continue
                        items.append({'path': str(path), 'root': str(root), 'group': area.id, 'chat': chat,
                                      'stat': fingerprint(info), 'bytes': allocated(info)})
            except OSError:
                errors.append('Some files could not be inspected. This area was left untouched.')
                items = []
            groups.append({'id': area.id, 'title': area.title, 'icon': area.icon, 'automatic': area.automatic,
                           'auto_supported': area.id in AUTO_AREAS,
                           'days': area.days, 'kind': area.kind, 'paths': [str(p) for p in area.roots],
                           'impact': area.impact, 'files': len(items), 'bytes': sum(p['bytes'] for p in items),
                           'blocked': errors[0] if errors else '',
                           'busy': area.id in ('pip','npm','staging') and inventory['package_busy']})
            candidates.extend(items)
        token = uuid.uuid4().hex
        disk = shutil.disk_usage(self.base)
        report = {'id': token, 'at': now, 'groups': groups, 'files': len(candidates),
                  'bytes': sum(c['bytes'] for c in candidates),
                  'automatic_bytes': sum(g['bytes'] for g in groups if g['automatic']),
                  'disk': {'total': disk.total, 'used': disk.used, 'free': disk.free}}
        atomic_json(self.state/'manifest.json', {'id': token, 'at': now, 'config': self.config, 'files': candidates})
        atomic_json(self.state/'report.json', report)
        return report

    @contextmanager
    def operation(self, label):
        try:
            with self.lock:
                atomic_json(self.state/'status.json', {'operation': label, 'started': self.clock()})
                try:
                    yield
                finally:
                    atomic_json(self.state/'status.json', {})
        except Timeout as exc:
            raise CleanerError('A0Cleaner is already working.') from exc

    def scan(self):
        with self.operation('Scanning'):
            return self._scan()

    def latest(self):
        status = read_json(self.state/'status.json', {})
        if status:
            try:
                with self.lock:
                    status = {}  # The previous process stopped before clearing its status.
            except Timeout:
                pass
        return {'report': read_json(self.state/'report.json'), 'status': status,
                'activity': read_json(self.state/'activity.json', []), 'config': self.config}

    def _selection(self, token, groups):
        if not isinstance(groups, list) or not groups or any(not isinstance(group, str) for group in groups):
            raise CleanerError('Select at least one cleanup area.')
        manifest = read_json(self.state/'manifest.json', {})
        report = read_json(self.state/'report.json', {})
        if not token or token != manifest.get('id') or token != report.get('id') or self.clock()-manifest['at'] > DAY:
            raise CleanerError('This scan is out of date. Scan again before cleaning.')
        if manifest.get('config') != self.config:
            raise CleanerError('Cleanup settings changed. Scan again before cleaning.')
        selected = [g for g in report['groups'] if g['id'] in groups]
        if len(selected) != len(set(groups)) or any(g['blocked'] for g in selected):
            raise CleanerError('This cleanup selection is unavailable. Scan again.')
        return selected, [f for f in manifest['files'] if f['group'] in groups]

    def preview(self, token, groups):
        with self.operation('Preparing cleanup'):
            selected, items = self._selection(token, groups)
            return {'id': token, 'groups': selected, 'files': len(items), 'bytes': sum(i['bytes'] for i in items),
                    'paths': [i['path'] for i in items[:200]], 'more_paths': max(0, len(items)-200)}

    def _delete(self, item, cutoff):
        path = Path(item['path'])
        with directory_fd(path.parent) as fd:
            info = os.stat(path.name, dir_fd=fd, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or fingerprint(info) != item['stat']:
                return False
            if max(info.st_mtime, info.st_ctime) >= cutoff:
                return False
            os.unlink(path.name, dir_fd=fd)
        return True

    def _clean(self, token, groups, *, automatic=False):
        selected, items = self._selection(token, groups)
        allowed = {area.id: area for area in self.areas()}
        if automatic and any(not allowed[g['id']].automatic for g in selected):
            raise CleanerError('This area requires manual confirmation.')
        inventory = self.process_inventory()
        self._mounts = set(inventory.get('mounts', []))
        eligible = {}
        for group in selected:
            area = allowed[group['id']]
            cutoff = self.clock()-area.days*DAY
            roots = {str(root) for root, _ in self._roots(area, cutoff, inventory)}
            if area.kind in ('profiles', 'versions'):
                for root in list(roots):
                    try:
                        if any(max(info.st_mtime, info.st_ctime) >= cutoff for _, info in self._walk(Path(root), {'files': 0, 'deadline': time.monotonic()+90})):
                            roots.remove(root)
                    except OSError:
                        roots.remove(root)
            eligible[area.id] = roots
        result = {'at': self.clock(), 'automatic': automatic, 'bytes': 0, 'files': 0, 'skipped': 0,
                  'areas': [g['title'] for g in selected], 'stopped': False}
        try:
            for item in items:
                self._check()
                area = allowed[item['group']]
                root = Path(item['root'])
                path = Path(item['path'])
                if not any(root.is_relative_to(base) for base in area.roots) or not path.is_relative_to(root) or any(part in PROTECTED_NAMES or part.startswith('.env.') for part in path.parts):
                    raise CleanerError('Cleanup manifest is invalid. Scan again.')
                blocked = str(root) not in eligible[area.id] or any(str(parent) in self._mounts for parent in (path, *path.parents) if parent != root and parent.is_relative_to(root))
                try:
                    blocked = blocked or path.lstat().st_uid in inventory.get('opaque_uids', [])
                except OSError:
                    blocked = True
                if item['chat']:
                    activity = self.chat_activity(item['chat'])
                    blocked = blocked or activity is None or activity >= self.clock()-area.days*DAY
                if blocked:
                    result['skipped'] += 1
                    continue
                try:
                    if self._delete(item, self.clock()-area.days*DAY):
                        result['files'] += 1
                        result['bytes'] += item['bytes']
                    else:
                        result['skipped'] += 1
                except OSError:
                    result['skipped'] += 1
        except CleanerError:
            result['stopped'] = True
            raise
        finally:
            activity = read_json(self.state/'activity.json', [])
            atomic_json(self.state/'activity.json', [result, *activity][:40])
            # A consumed manifest can never authorize a second deletion pass.
            atomic_json(self.state/'manifest.json', {})
        return result

    def clean(self, token, groups, *, confirmed=False):
        if confirmed is not True:
            raise CleanerError('Confirm the selected cleanup areas first.')
        with self.operation('Cleaning'):
            result = self._clean(token, groups)
            report = self._scan()
            return {'result': result, 'report': report}

    def scheduled(self):
        with self.operation('Scheduled maintenance'):
            report = self._scan()
            result = None
            groups = [g['id'] for g in report['groups'] if g['automatic'] and g['files'] and not g['blocked']]
            if self.config['automatic'] and groups:
                result = self._clean(report['id'], groups, automatic=True)
                report = self._scan()
            summary = {'at': self.clock(), 'found_bytes': report['bytes'], 'freed_bytes': result['bytes'] if result else 0,
                       'skipped': result['skipped'] if result else 0, 'report_id': report['id']}
            atomic_json(self.state/'scheduled.json', summary)
            return summary
