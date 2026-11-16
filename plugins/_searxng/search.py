"""Web search CLI: python -m plugins._searxng.search QUERY (or --status)."""
from contextlib import contextmanager
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from filelock import FileLock, Timeout
from helpers.sandbox import SandboxError, SandboxMount, get_manager

NAME = 'service-searxng'
PLUGIN = Path(__file__).resolve().parent
SUPPORT = PLUGIN.parent / '_sandboxing' / 'sandbox'
NOTICE = 'Preparing search sandbox. First use may take a little while to install dependencies.'


def _paths(manager):
    directory = manager.config.instances_dir / '.searxng-cli'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return FileLock(directory / 'lock'), directory / 'status.json'


def _read_status(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {'state': 'idle'}


def _write_status(path, state, message):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps({'state': state, 'message': message, 'updated_at': time.time()}))
    temporary.replace(path)


def status(manager):
    lock, path = _paths(manager)
    try:
        with lock.acquire(timeout=0):
            result = _read_status(path)
            if result['state'] not in ('idle', 'error'):
                result = {'state': 'interrupted', 'message': 'Previous call ended; the next query will retry setup.'}
            return {**result, 'busy': False}
    except Timeout:
        return {**_read_status(path), 'busy': True}


@contextmanager
def locked(manager):
    lock, path = _paths(manager)
    try:
        lock.acquire(timeout=0)
    except Timeout:
        print('Waiting for search sandbox: ' + json.dumps(status(manager)), file=sys.stderr, flush=True)
        lock.acquire(timeout=2100)
    try:
        yield path
    finally:
        lock.release()


def _execute(manager, argv, timeout):
    result = manager.exec(NAME, argv, timeout=timeout)
    if result.exit_code:
        raise SandboxError((result.stderr or result.stdout or f'Guest exited {result.exit_code}')[-6000:])
    return result.stdout


def search(query, manager):
    if not isinstance(query, str) or not query.strip() or len(query) > 8192:
        raise ValueError('Search query must contain between 1 and 8192 characters')
    with locked(manager) as state:
        _write_status(state, 'starting', NOTICE)
        print(NOTICE, file=sys.stderr, flush=True)
        exists = (manager.config.instances_dir / NAME / 'metadata.json').is_file()
        mounts = [SandboxMount(PLUGIN, '/plugin'), SandboxMount(SUPPORT, '/worker')]
        try:
            try:
                if exists:
                    manager.stop(NAME)
                    manager.set_command(NAME, [])
                    manager.set_mounts(NAME, mounts)
                    manager.start(NAME)
                else:
                    manager.create(NAME, sandbox_type='permanent', service=True, share_usr=False, mounts=mounts)
                    exists = True
                fingerprint = hashlib.sha256(b'\0'.join(path.read_bytes() for path in (
                    PLUGIN / 'sandbox/install.sh', PLUGIN / 'sandbox/requirements.txt', SUPPORT / 'constraints.txt',
                ))).hexdigest()
                try:
                    installed = manager.read_file(NAME, 'var/lib/a0-worker/installed').strip()
                except (OSError, SandboxError):
                    installed = ''
                if installed != fingerprint:
                    _write_status(state, 'installing', 'Installing SearXNG in image Python; concurrent queries wait.')
                    _execute(manager, ['sh', '/plugin/sandbox/setup.sh', fingerprint], 1800)
                # shortcut: each CLI call imports SearXNG anew; use a persistent worker if query volume warrants it.
                _write_status(state, 'searching', 'Searching the web')
                result = json.loads(_execute(manager, ['python', '/plugin/sandbox/search.py', query], 60))
                if not isinstance(result, dict) or not isinstance(result.get('results'), list):
                    raise ValueError('SearXNG returned an invalid search response')
            finally:
                if exists:
                    manager.stop(NAME)
        except BaseException:
            _write_status(state, 'error', 'Search failed or interrupted; see command output and retry to resume setup.')
            raise
        _write_status(state, 'idle', 'Search finished; installation retained for the next query.')
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', nargs='?')
    parser.add_argument('--status', action='store_true', help='Show current setup/query status without waiting or starting a sandbox')
    args = parser.parse_args(argv)
    if (args.status and args.query is not None) or (not args.status and not args.query):
        parser.error('provide a query or --status')
    from helpers import dotenv
    dotenv.load_dotenv()
    try:
        manager = get_manager()
        result = status(manager) if args.status else search(args.query, manager)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0
    except (SandboxError, OSError, ValueError, Timeout) as exc:
        print(json.dumps({'error': str(exc)}), flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
