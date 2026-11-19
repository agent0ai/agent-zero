"""Opt-in real runtime checks: A0_PROOT_INTEGRATION=1 pytest tests/test_proot_runtime.py."""
import dataclasses
import json
import os
from pathlib import Path
import subprocess
import time

import pytest

from plugins._sandboxing.helpers.images import SandboxImageConfig, SandboxImageManager
from plugins._sandboxing.helpers.manager import SandboxConfig, SandboxManager, SandboxMount, SandboxError
from plugins._sandboxing.helpers import storage
from plugins._sandboxing.helpers.builtin_image import BUILTIN_IMAGE

pytestmark = pytest.mark.skipif(os.environ.get('A0_PROOT_INTEGRATION') != '1', reason='requires disposable Linux root container and built PRoot')


@pytest.fixture(scope='module')
def manager(tmp_path_factory):
    root = tmp_path_factory.mktemp('proot')
    images = SandboxImageManager(SandboxImageConfig(
        skopeo=Path('/usr/bin/skopeo'), umoci=Path('/usr/bin/umoci'),
        cache_dir=root/'images', default_image=os.environ.get('A0_PROOT_TEST_IMAGE', BUILTIN_IMAGE)))
    image = images.ensure(images.config.default_image)
    fixtures = image.rootfs/'cow-tests'
    fixtures.mkdir()
    for name in ('write', 'chmod', 'fdchmod', 'time', 'fdtime', 'xattr', 'link', 'rename', 'access', 'access-readonly'):
        (fixtures/name).write_text('original')
    (fixtures/'access-readonly').chmod(0o444)
    (fixtures/'denied-parent').mkdir()
    (fixtures/'denied-parent/file').write_text('original')
    os.link(fixtures/'link', fixtures/'alias')
    os.setxattr(fixtures/'write', 'user.test', b'preserved')
    runtime = SandboxManager(SandboxConfig(
        proot=Path('/usr/local/bin/a0-proot'), instances_dir=root/'instances',
        uid_registry=root/'uids', shared_dir=root/'shared', default_image=images.config.default_image), images)
    yield runtime
    for info in runtime.list():
        runtime.delete(info.name)


def run(manager, name, script):
    result = manager.exec(name, ['python', '-c', script])
    assert result.exit_code == 0, result.stderr + result.stdout
    return result.stdout


def test_copy_on_write_and_peer_persistence(manager):
    manager.create('alpha')
    manager.create('beta')
    root = manager.config.instances_dir/'alpha/rootfs'
    other = manager.config.instances_dir/'beta/rootfs'
    assert (root/'cow-tests/write').stat().st_ino == (other/'cow-tests/write').stat().st_ino
    run(manager, 'alpha', '''
import os
from pathlib import Path
p=Path('/cow-tests')
(p/'write').write_text('private')
assert os.getxattr(p/'write','user.test') == b'preserved'
os.chmod(p/'chmod',0o600)
f=os.open(p/'fdchmod',os.O_RDONLY); os.fchmod(f,0o600); os.close(f)
os.utime(p/'time',(1234567890,1234567890))
f=os.open(p/'fdtime',os.O_RDONLY); os.utime(f,(1234567890,1234567890)); os.close(f)
os.setxattr(p/'xattr','user.test',b'value')
(p/'link').write_text('linked'); assert (p/'alias').read_text()=='linked'
(p/'rename').rename(p/'renamed'); (p/'renamed').write_text('renamed')
''')
    assert (other/'cow-tests/write').read_text() == 'original'
    assert (other/'cow-tests/fdchmod').stat().st_mode & 0o777 == 0o644
    assert (root/'cow-tests/fdchmod').stat().st_mode & 0o777 == 0o600
    assert (root/'cow-tests/fdtime').stat().st_mtime == 1234567890
    assert manager.disk_usage('alpha') < 30 * 1024 * 1024
    manager.stop('alpha'); manager.start('alpha')
    assert run(manager, 'alpha', "print(open('/cow-tests/write').read())").strip() == 'private'



def test_access_probes_match_copy_up_without_copying(manager):
    manager.create('permissions')
    root = manager.config.instances_dir/'permissions/rootfs'
    target = root/'cow-tests/access'
    before = target.stat()
    os.chown(root/'cow-tests/denied-parent',0,0)
    (root/'cow-tests/denied-parent').chmod(0o555)
    run(manager, 'permissions', r"""
import ctypes, os, platform
from pathlib import Path
p = Path('/cow-tests/access')
assert os.access(p, os.W_OK)
assert os.access(p, os.R_OK | os.W_OK)
assert not os.access(p, os.W_OK | os.X_OK)
assert not os.access('/cow-tests/missing', os.W_OK)
assert not os.access('/cow-tests/access-readonly', os.W_OK)
assert not os.access('/cow-tests/denied-parent/file', os.W_OK)
fd = os.open('/cow-tests', os.O_RDONLY | os.O_DIRECTORY)
assert os.access('access', os.W_OK, dir_fd=fd, effective_ids=True)
os.symlink('access', '/cow-tests/probe-link')
assert os.access('/cow-tests/probe-link', os.W_OK)
libc = ctypes.CDLL(None, use_errno=True)
assert libc.access(b'/cow-tests/access', os.W_OK) == 0
# Exercise the legacy syscall separately from glibc's faccessat2 wrapper.
legacy = {'x86_64':269, 'aarch64':48}[platform.machine()]
assert libc.syscall(legacy, fd, b'access', os.W_OK) == 0
assert libc.syscall(439, fd, b'access', os.W_OK, 0x200) == 0
assert libc.syscall(439, fd, b'access', 8, 0) == -1
assert libc.syscall(439, fd, b'access', os.W_OK, 0x4000) == -1
os.close(fd)
""")
    after = target.stat()
    assert (before.st_dev, before.st_ino, before.st_uid) == (after.st_dev, after.st_ino, after.st_uid)
    run(manager, 'permissions', "open('/cow-tests/access','a').write(' changed')")
    assert target.read_text() == 'original changed'
    assert target.stat().st_ino != before.st_ino
    # PRoot's existing fake-root handling of UID-owned private files is retained.
    run(manager, 'permissions', "import os; os.chmod('/cow-tests/access',0o400); assert os.access('/cow-tests/access',os.W_OK); open('/cow-tests/access','a').write(' private')")

def test_readonly_bindings_and_atomic_request_acl(manager):
    directory = manager.config.instances_dir.parent/'input'
    directory.mkdir(mode=0o700)
    (directory/'request').write_text('initial')
    manager.create('bindings', service=True, share_usr=False, mounts=[SandboxMount(directory,'/input')])
    temporary=directory/'temporary'
    temporary.write_text('replacement')
    temporary.chmod(0o640)
    temporary.replace(directory/'request')
    run(manager,'bindings','''
import os
assert open('/input/request').read()=='replacement'
for mutate in [lambda: open('/input/request','w'),lambda: os.unlink('/input/request'),lambda: os.chmod('/input/request',0o777),lambda: os.mkdir('/input/new')]:
    try: mutate()
    except OSError: pass
    else: raise AssertionError('read-only mutation succeeded')
''')
    assert (directory/'request').read_text() == 'replacement'
    run(manager,'bindings',"import os; assert not os.access('/input/request',os.W_OK)")
    uid=manager._read_metadata('bindings')['uid']
    storage.grant(directory,uid,writable=True)
    storage.traverse(directory/'request',uid)
    run(manager,'bindings',"import os; assert not os.access('/input/request',os.W_OK)")
    subprocess.run(['setpriv',f'--reuid={uid}',f'--regid={uid}','--clear-groups','sh','-c',f'touch {directory}/allowed'],check=True)


def test_network_none_and_timeout_cleanup(manager):
    manager.create('offline',network='none')
    run(manager,'offline','''
import socket, os, struct
socket.socket(socket.AF_UNIX)
a,b=socket.socketpair()
a.sendmsg([b'x'],[(socket.SOL_SOCKET,socket.SCM_CREDENTIALS,struct.pack('3i',os.getpid(),os.getuid(),os.getgid()))])
assert b.recv(1)==b'x'
a.close();b.close()
try: socket.socket(socket.AF_INET)
except PermissionError: pass
else: raise AssertionError('IP socket allowed')
''')
    with pytest.raises(SandboxError,match='timed out'):
        manager.exec('offline',['python','-c',"import os,time,ctypes; os.fork(); os.setsid(); open('/workspace/timeout-pid','w').write(str(os.getpid())); ctypes.CDLL(None).prctl(4,0); time.sleep(60)"],timeout=.5)
    pid=int((manager.config.instances_dir/'offline/rootfs/workspace/timeout-pid').read_text())
    assert not Path(f'/proc/{pid}').exists()
    assert manager.is_running('offline')
    assert run(manager,'offline',"print('alive')").strip()=='alive'


def test_quick_commands_and_restart(manager):
    manager.create('quick',command=['/bin/sh','-c','echo done > /workspace/done'])
    deadline=time.monotonic()+5
    while manager.is_running('quick') and time.monotonic()<deadline: time.sleep(.05)
    assert not manager.is_running('quick')
    assert (manager.config.instances_dir/'quick/rootfs/workspace/done').read_text()=='done\n'
    manager.start('quick')
    time.sleep(.3)
    assert not manager.is_running('quick')


def test_parent_exit_and_standalone_restore(manager, tmp_path):
    script=tmp_path/'parent.py'
    script.write_text('''
import json
from pathlib import Path
from plugins._sandboxing.helpers.images import SandboxImageConfig,SandboxImageManager
from plugins._sandboxing.helpers.manager import SandboxConfig,SandboxManager
values=json.loads(__import__('sys').argv[1])
for key in ['proot','instances_dir','uid_registry','shared_dir']:values[key]=Path(values[key])
images=SandboxImageManager(SandboxImageConfig(skopeo=Path('/usr/bin/skopeo'),umoci=Path('/usr/bin/umoci'),cache_dir=values['instances_dir'].parent/'images',default_image=values['default_image']))
m=SandboxManager(SandboxConfig(**values),images)
m.create('child-exit')
m.create('standalone',standalone=True)
''')
    config=dataclasses.asdict(manager.config)
    subprocess.run([__import__('sys').executable,str(script),json.dumps(config,default=str)],check=True,env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1])})
    deadline=time.monotonic()+8
    while manager.is_running('child-exit') and time.monotonic()<deadline:time.sleep(.05)
    assert not manager.is_running('child-exit')
    assert manager.is_running('standalone')
    restored=SandboxManager(manager.config,manager.images)
    assert run(restored,'standalone',"print('restored')").strip()=='restored'
    restored.stop('standalone')
    assert restored.inspect('standalone').desired_running is False


def test_socket_across_exec_and_legacy_disk_migration(manager):
    import shutil
    manager.create('legacy')
    path=manager.config.instances_dir/'legacy'
    manager.stop('legacy')
    # Model the old full-copy root, without introducing shared base inodes.
    shutil.copytree(path/'rootfs',path/'private',symlinks=True)
    shutil.rmtree(path/'rootfs');(path/'private').rename(path/'rootfs')
    value=manager._read_metadata('legacy')
    value.update(schema_version=2,filesystem='disk');value.pop('uid')
    manager._atomic_write_json(path/'metadata.json',value)
    manager.start('legacy')
    assert manager._read_metadata('legacy')['schema_version']==3
    command=manager.process_command('legacy',['python','-c',"import socket; s=socket.socket(socket.AF_UNIX); s.bind('/tmp/test.sock'); s.listen(); c,_=s.accept(); c.send(b'ok')"])
    server=subprocess.Popen(command)
    try:
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            result=manager.exec('legacy',['python','-c',"import socket; s=socket.socket(socket.AF_UNIX); s.connect('/tmp/test.sock'); assert s.recv(2)==b'ok'"])
            if result.exit_code==0:break
            time.sleep(.05)
        assert result.exit_code==0,result.stderr
        assert server.wait(timeout=5)==0
    finally:
        if server.poll() is None:server.terminate();server.wait(timeout=8)


def test_destination_files_use_guest_paths_mounts_and_binary_limits(manager, monkeypatch, tmp_path):
    import asyncio
    from types import SimpleNamespace

    from helpers import destination_files
    from plugins._code_execution.helpers.destinations import ExecutionDestination
    from plugins._sandboxing.helpers import runtime
    from plugins._text_editor.tools import text_editor

    mounted = tmp_path / "read-only"
    mounted.mkdir()
    (mounted / "data").write_bytes(b"mounted")
    manager.create("file-edit", mounts=[SandboxMount(mounted, "/input")])
    manager.create("file-service", service=True)
    agent = SimpleNamespace(data={}, read_prompt=lambda name, **values: f"{name} {values}")

    async def no_extensions(*args, **kwargs):
        pass

    monkeypatch.setattr(text_editor, "call_extensions_async", no_extensions)
    monkeypatch.setattr(text_editor, "_get_config", lambda _: {
        "max_line_tokens": 500, "default_line_count": 100, "max_total_read_tokens": 4000,
    })
    monkeypatch.setattr(runtime, "get_manager", lambda **kwargs: manager)
    monkeypatch.setattr(runtime, "defaults", lambda **kwargs: ("file-edit", "temporary", "host"))

    async def resolve(_agent, name):
        return ExecutionDestination(name, "sandbox", name, "", target=name)

    monkeypatch.setattr(destination_files, "resolve", resolve)

    async def check():
        name, path = "file-edit", "/workspace/private/data"
        revision = await destination_files.write(agent, name, path, b"\x00old\xff", limit=64)
        assert await destination_files.read(agent, name, path, limit=64) == b"\x00old\xff"
        await destination_files.write(agent, name, path, b"new", limit=64, expected=revision)
        with pytest.raises(OSError, match="changed since"):
            await destination_files.write(agent, name, path, b"lose", limit=64, expected=revision)
        with pytest.raises(OSError, match="exceeds 2 bytes"):
            await destination_files.read(agent, name, path, limit=2)
        assert await destination_files.read(agent, name, "/input/data", limit=64) == b"mounted"
        with pytest.raises(OSError):
            await destination_files.write(agent, name, "/input/data", b"changed", limit=64)
        with pytest.raises(PermissionError, match="service sandboxes"):
            await destination_files.read(agent, "file-service", path, limit=64)
        assert await destination_files.read(agent, name, path, limit=64) == b"new"

        async def edit(action, **kwargs):
            args = {"action": action, "destination": name, "path": path, **kwargs}
            return await text_editor.TextEditor(agent, "text_editor", None, args, "", None).execute(**args)

        assert "new" in (await edit("read")).message
        assert "patched" in (await edit("patch", old_text="new", new_text="live edit")).message
        assert await destination_files.read(agent, name, path, limit=64) == b"live edit"

    asyncio.run(check())
    assert (mounted / "data").read_bytes() == b"mounted"
