"""PRoot subprocess entry point. Run directly so no framework imports reach children."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time


def identity(pid: int) -> str | None:
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return None if fields[0] == 'Z' else fields[19]
    except (OSError, IndexError):
        return None


def alive(state: dict) -> bool:
    pid = state.get('pid')
    return isinstance(pid, int) and pid > 1 and identity(pid) == state.get('start') and state.get('start') is not None


def user_processes(uid: int):
    for path in Path('/proc').iterdir():
        if path.name.isdigit():
            try:
                if real_uid(path) == uid and identity(int(path.name)):
                    yield int(path.name)
            except OSError:
                pass


def real_uid(process: Path) -> int | None:
    # /proc directory ownership becomes root when a process disables core dumps.
    try:
        for line in (process / 'status').read_text().splitlines():
            if line.startswith('Uid:'):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return None


def terminate_uid(uid: int, timeout: float = 3) -> None:
    if not 20000 <= uid < 60000:
        raise ValueError('Invalid sandbox UID')
    for signum, delay in ((signal.SIGTERM, timeout), (signal.SIGKILL, 1)):
        for pid in user_processes(uid):
            try:
                os.kill(pid, signum)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + delay
        while time.monotonic() < deadline and any(user_processes(uid)):
            time.sleep(.05)
    if any(user_processes(uid)):
        raise RuntimeError('Sandbox processes did not stop')


def terminate_children() -> None:
    """As subreaper, collect even commands which double-fork or create sessions."""
    for signum in (signal.SIGTERM, signal.SIGKILL):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            parents = {}
            for path in Path('/proc').iterdir():
                if path.name.isdigit():
                    try:
                        fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
                        parents[int(path.name)] = int(fields[1])
                    except (OSError, ValueError, IndexError):
                        pass
            children = {os.getpid()}
            while True:
                found = {pid for pid, parent in parents.items() if parent in children} - children
                if not found:
                    break
                children.update(found)
            children.discard(os.getpid())
            for pid in children:
                try:
                    os.kill(pid, signum)
                except ProcessLookupError:
                    pass
            try:
                while os.waitpid(-1, os.WNOHANG)[0]:
                    pass
            except ChildProcessError:
                return
            time.sleep(.05)


def syscall_policy(network: str) -> None:
    """Deny creating IP/packet sockets in the kernel; local Unix IPC remains available."""
    library = ctypes.CDLL('libseccomp.so.2', use_errno=True)
    library.seccomp_init.restype = ctypes.c_void_p
    library.seccomp_init.argtypes = [ctypes.c_uint32]
    library.seccomp_rule_add_array.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint, ctypes.c_void_p]
    library.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    library.seccomp_load.argtypes = [ctypes.c_void_p]
    library.seccomp_release.argtypes = [ctypes.c_void_p]
    class Compare(ctypes.Structure):
        _fields_ = [('arg', ctypes.c_uint), ('op', ctypes.c_int), ('a', ctypes.c_uint64), ('b', ctypes.c_uint64)]
    context = library.seccomp_init(0x7fff0000)
    if not context:
        raise RuntimeError('Cannot create offline syscall policy')
    try:
        for name in ((b'socket', b'socketpair') if network == 'none' else ()):
            number = library.seccomp_syscall_resolve_name(name)
            condition = Compare(0, 1, 1, 0)  # SCMP_CMP_NE, AF_UNIX
            if number < 0 or library.seccomp_rule_add_array(context, 0x50001, number, 1, ctypes.byref(condition)) < 0:
                raise RuntimeError('Cannot configure offline syscall policy')
        # PRoot 5.5 does not translate these path/open interfaces; force libc fallback.
        for name in (b'openat2', b'io_uring_setup'):
            number = library.seccomp_syscall_resolve_name(name)
            if number >= 0 and library.seccomp_rule_add_array(context, 0x50026, number, 0, None) < 0:
                raise RuntimeError('Cannot configure PRoot syscall fallback')
        if library.seccomp_load(context) < 0:
            raise RuntimeError('Cannot apply offline syscall policy')
    finally:
        library.seccomp_release(context)


def guest(fd: int) -> None:
    with os.fdopen(fd) as handle:
        config = json.load(handle)
    if os.getuid() != config['uid'] or not 20000 <= os.getuid() < 60000:
        raise RuntimeError('Sandbox privileges were not dropped')
    if ctypes.CDLL(None, use_errno=True).prctl(38, 1, 0, 0, 0):
        raise RuntimeError('Cannot set no_new_privs')
    syscall_policy(config['network'])
    bindings = [value for source, destination in config['bindings'] for value in ('-b', source + ':' + destination + '!')]
    environment = dict(config['environment'])
    environment.update(A0_COW_ROOT=config['root'], A0_COW_CONTROL=config['control'],
                       A0_READONLY_PATHS='\n'.join(config['readonly']), PROOT_TMP_DIR=config['temp'])
    argv = [config['proot'], '-0', '-r', config['root'], *bindings, '-w', config['cwd'], *config['command']]
    os.execve(config['proot'], argv, environment)


def run(config_path: Path, *, owner_fd: int | None = None, argv=None, cwd=None) -> int:
    if os.geteuid() != 0:
        raise PermissionError('Sandbox launcher must run as root')
    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0):  # PR_SET_CHILD_SUBREAPER
        raise RuntimeError('Cannot supervise sandbox descendants')
    config = json.loads(config_path.read_text())
    main = argv is None
    if not main:
        config.update(command=argv, cwd=cwd)
        state = json.loads((config_path.parent / 'state.json').read_text())
        if not alive(state):
            raise RuntimeError('Sandbox is stopped')
    fd = os.memfd_create('a0-sandbox-config', os.MFD_CLOEXEC)
    os.write(fd, json.dumps(config).encode()); os.lseek(fd, 0, os.SEEK_SET)
    stopping = False
    def stop(*_):
        nonlocal stopping
        stopping = True
    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, stop)
    child = None
    try:
        child = subprocess.Popen([sys.executable, '-c', Path(__file__).read_text(), 'guest', str(fd)],
                                 pass_fds=(fd,), user=config['uid'], group=config['uid'], extra_groups=[],
                                 env={'PATH': '/usr/local/bin:/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'},
                                 cwd='/', start_new_session=True)
        os.close(fd); fd = -1
        if main:
            state_path = config_path.parent / 'state.json'
            temp = state_path.with_suffix('.tmp')
            temp.write_text(json.dumps({'pid': os.getpid(), 'start': identity(os.getpid())}))
            temp.chmod(0o600); temp.replace(state_path)
        while child.poll() is None and not stopping:
            if owner_fd is not None:
                ready, _, _ = select.select([owner_fd], [], [], .1)
                if ready and not os.read(owner_fd, 1024):
                    break
            else:
                time.sleep(.05)
        return child.returncode if child.returncode is not None else 128 + signal.SIGTERM
    finally:
        if fd >= 0:
            os.close(fd)
        if main:
            terminate_uid(config['uid'])
            state_path = config_path.parent / 'state.json'
            temporary = state_path.with_suffix('.tmp')
            temporary.write_text(json.dumps({'status': 'stopped', 'exit_code': child.returncode if child else 1}))
            temporary.chmod(0o600); temporary.replace(state_path)
        else:
            terminate_children()
        if child:
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill(); child.wait(timeout=3)


if __name__ == '__main__':
    if sys.argv[1] == 'guest':
        guest(int(sys.argv[2]))
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument('mode', choices=('supervise', 'execute'))
        parser.add_argument('config', type=Path)
        parser.add_argument('--owner-fd', type=int)
        parser.add_argument('--cwd', default='/workspace')
        parser.add_argument('command', nargs=argparse.REMAINDER)
        args = parser.parse_args()
        command = args.command
        if command[:1] == ['--']:
            command = command[1:]
        sys.exit(run(args.config, owner_fd=args.owner_fd,
                     argv=command if args.mode == 'execute' else None, cwd=args.cwd))
