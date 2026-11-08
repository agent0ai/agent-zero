"""Own the loopback Tuxee server; Linux PAM remains its session boundary."""
import atexit
import hashlib
import os
from pathlib import Path
import socket
import subprocess
import threading
import time
import urllib.request
from helpers import files

_lock = threading.RLock()
_process = None
_port = 0
BUILD = Path(__file__).resolve().parents[1] / 'build'
BINARY = Path('/usr/local/lib/tuxee/tuxee')


def build_id():
    records = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(BUILD)}\n'
                      for p in sorted(BUILD.rglob('*')) if p.is_file())
    return hashlib.sha256(''.join(sorted(records.splitlines(keepends=True))).encode()).hexdigest()


def ensure_installed():
    marker = BINARY.parent / 'a0-build-id'
    if BINARY.is_file() and marker.is_file() and marker.read_text().strip() == build_id():
        return
    from plugins._desktop.helpers.install import install
    install()


def status():
    return {'ok': True, 'running': bool(_process and _process.poll() is None),
            'installed': BINARY.is_file(), 'url': '/desktop/tuxee/'}


def start():
    global _process, _port
    with _lock:
        if _process and _process.poll() is None:
            return _port
        ensure_installed()
        state = Path(files.get_abs_path('usr/plugins/_desktop/tuxee'))
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
        state.chmod(0o700)
        # Dedicated empty config prevents global listener settings from overriding loopback.
        config = state / 'managed-config.json'
        config.write_text('{}\n')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            _port = sock.getsockname()[1]
        env = {key: value for key, value in os.environ.items() if not key.startswith('TUXEE_')}
        with (state / 'server.log').open('ab') as log:
            _process = subprocess.Popen([str(BINARY), 'serve', '--config', str(config), '--http',
                '--bind', f'127.0.0.1:{_port}', '--state', str(state)], env=env, stdout=log, stderr=log)
        for _ in range(100):
            if _process.poll() is not None:
                raise RuntimeError('Tuxee exited during startup; see Desktop server.log')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{_port}/health', timeout=.5) as response:
                    if response.status == 200:
                        return _port
            except OSError:
                time.sleep(.1)
        stop()
        raise RuntimeError('Tuxee startup timed out')


def stop():
    global _process
    with _lock:
        if _process and _process.poll() is None:
            _process.terminate()
            try:
                _process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                _process.kill()
                _process.wait()
        _process = None


atexit.register(stop)
