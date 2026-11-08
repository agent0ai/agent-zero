"""Private Chromium display using the same minimal Xvnc runtime as Tuxee."""
from __future__ import annotations

import configparser
import os
from pathlib import Path
import secrets
import select
import shutil
import socket
import struct
import subprocess
import threading
import time
import uuid

from helpers import native_display

DEFAULT_WIDTH, DEFAULT_HEIGHT = 1024, 768
_keyboard = {}


def keyboard_options():
    return _keyboard


def collect_status():
    binaries = {name: shutil.which(name) or '' for name in ('tuxee-Xvnc', 'tuxee-vncpasswd', 'xrandr')}
    missing = [name for name, path in binaries.items() if not path]
    return {'available': not missing, 'missing': missing, 'binaries': binaries}


class BrowserInteractiveView:
    def __init__(self, context_id):
        self.context_id = str(context_id)
        self.token = 'browser-' + uuid.uuid4().hex
        self.state_dir = Path('/run/a0-browser') / self.token
        self.display = None
        self.port = 0
        self.password = ''
        self.width, self.height = DEFAULT_WIDTH, DEFAULT_HEIGHT
        self._server = None
        self._lock = threading.RLock()

    @property
    def display_name(self):
        return f':{self.display}' if self.display is not None else ''

    @property
    def xauthority(self):
        return str(self.state_dir / 'Xauthority')

    @property
    def gtk_config(self):
        return str(self.state_dir / 'gtk')

    def _fit_file_dialog(self):
        # Without a window manager, GTK's default picker can exceed the display.
        path = Path(self.gtk_config) / 'glib-2.0/settings/keyfile'
        path.parent.mkdir(parents=True, exist_ok=True)
        settings = configparser.ConfigParser(interpolation=None)
        settings.read(path)
        section = 'org/gtk/settings/file-chooser'
        if not settings.has_section(section):
            settings.add_section(section)
        settings[section].update({'window-size': f'({self.width}, {self.height})', 'window-position': '(0, 0)'})
        temporary = path.with_suffix('.tmp')
        with temporary.open('w') as stream:
            settings.write(stream)
        temporary.replace(path)

    def _env(self):
        return {**os.environ, 'DISPLAY': self.display_name, 'XAUTHORITY': self.xauthority, 'XKB_CONFIG_ROOT': '/opt/tuxee-gui/xkb'}

    def _write_xauthority(self, cookie, number=''):
        fields = (b'', str(number).encode(), b'MIT-MAGIC-COOKIE-1', cookie)
        payload = struct.pack('>H', 65535) + b''.join(struct.pack('>H', len(v)) + v for v in fields)
        with open(self.xauthority, 'wb') as stream:
            os.chmod(self.xauthority, 0o600)
            stream.write(payload)

    def ensure_display(self):
        with self._lock:
            if self._running(self._server) and self.display is not None:
                return self.display_name
            self._stop_locked()
            status = collect_status()
            if not status['available']:
                raise RuntimeError('Browser display needs: ' + ', '.join(status['missing']))
            self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.state_dir.chmod(0o700)
            self._fit_file_dialog()
            self.password = secrets.token_urlsafe(6)
            passwd = self.state_dir / 'passwd'
            with passwd.open('wb') as stream:
                passwd.chmod(0o600)
                subprocess.run(['tuxee-vncpasswd', '-f'], input=(self.password + '\n').encode(),
                               stdout=stream, stderr=subprocess.PIPE, check=True, timeout=5)
            cookie = secrets.token_bytes(16)
            self._write_xauthority(cookie)
            self.port = self._free_port()
            read_fd, write_fd = os.pipe()
            try:
                with (self.state_dir / 'display.log').open('ab') as log:
                    self._server = subprocess.Popen([
                        'tuxee-Xvnc', '-displayfd', str(write_fd), '-geometry', f'{self.width}x{self.height}',
                        '-depth', '24', '-rfbport', str(self.port), '-interface', '127.0.0.1',
                        '-localhost', '-SecurityTypes', 'VncAuth', '-PasswordFile', str(passwd),
                        '-AlwaysShared', '-DisconnectClients=0', '-SendPrimary=0', '-SetPrimary=0',
                        '-auth', self.xauthority, '-nolisten', 'tcp', '-extension', 'MIT-SHM',
                        '-fp', 'built-ins', '-xkbdir', '/opt/tuxee-gui/xkb', '-s', '0', '-noreset',
                    ], stdin=subprocess.DEVNULL, stdout=log, stderr=log, pass_fds=(write_fd,), env={**os.environ, 'XKB_BINDIR': '/opt/tuxee-gui/bin'})
            except BaseException:
                os.close(read_fd)
                self._stop_locked()
                raise
            finally:
                os.close(write_fd)
            try:
                readable, _, _ = select.select([read_fd], [], [], 10)
                number = os.read(read_fd, 32).decode().strip() if readable else ''
                if not number.isdigit() or not self._running(self._server):
                    raise RuntimeError('Xvnc did not become ready; see sandbox display.log')
                self.display = int(number)
                self._write_xauthority(cookie, number)
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if native_display.current_display_size(self.display, env=self._env()):
                        break
                    time.sleep(.05)
                else:
                    raise RuntimeError('Browser X display did not accept its private credentials')
                self._apply_keyboard_layout()
                return self.display_name
            except BaseException:
                self._stop_locked()
                raise
            finally:
                os.close(read_fd)

    def ensure_viewer(self, width=0, height=0):
        with self._lock:
            self.ensure_display()
            self.resize(width or self.width, height or self.height)
            return {'available': True, 'port': self.port, 'password': self.password,
                    'width': self.width, 'height': self.height}

    def resize(self, width, height):
        with self._lock:
            width, height = native_display.normalize_size(width, height)
            if self.display is None or not self._running(self._server):
                self.width, self.height = width, height
                return {'ok': False, 'error': 'Browser display is unavailable.',
                        'width': self.width, 'height': self.height}
            # A0 owns this private display; repeated viewer requests need no X client.
            if (width, height) == (self.width, self.height):
                return {'ok': True, 'width': width, 'height': height, 'resized': False}
            result = native_display.resize_display(display=self.display, width=width, height=height,
                                                   settle_seconds=0, env=self._env())
            if result.get('ok'):
                self.width, self.height = width, height
                self._fit_file_dialog()
            return result

    def _apply_keyboard_layout(self):
        options = keyboard_options()
        if self.display is None or not options.get('layout'):
            return
        command = [shutil.which('setxkbmap') or 'setxkbmap', '-display', self.display_name, '-layout', options['layout'], '-I/opt/tuxee-gui/xkb']
        if options.get('variant'):
            command.extend(['-variant', options['variant']])
        subprocess.run(command, env=self._env(), check=True, capture_output=True, timeout=5)

    def close(self):
        with self._lock:
            self._stop_locked()
            shutil.rmtree(self.state_dir, ignore_errors=True)

    def _stop_locked(self):
        if self._running(self._server):
            self._server.terminate()
            try:
                self._server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._server.kill()
                self._server.wait(timeout=2)
        self._server = None
        self.display = None
        self.port = 0
        self.password = ''

    @staticmethod
    def _running(process):
        return process is not None and process.poll() is None

    @staticmethod
    def _free_port():
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            return probe.getsockname()[1]
