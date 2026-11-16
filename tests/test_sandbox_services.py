from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path

import pytest

from tests.test_sandboxing import manager, _metadata
from plugins._sandboxing.helpers.manager import SandboxError, SandboxManager, SandboxMount


def create_disk(manager, monkeypatch, **kwargs):
    monkeypatch.setattr(manager, '_launch', lambda *args: None)
    monkeypatch.setattr(manager, '_runtime_state', lambda *args: ({'status': 'running'}, None))
    manager.create('service', **kwargs)
    return manager._read_metadata('service')


def test_disk_root_survives_missing_runtime_without_snapshot(manager, monkeypatch):
    metadata = create_disk(manager, monkeypatch, standalone=True)
    root = manager.config.instances_dir / 'service' / 'rootfs'
    (root / 'workspace' / 'proof').write_text('survives abrupt exit')
    assert metadata['rootfs_snapshot'] is None
    monkeypatch.setattr(manager, '_runtime_state', lambda *args: (None, 'container not found'))
    assert manager.inspect('service').status == 'recoverable'
    launched = []
    monkeypatch.setattr(manager, '_launch', lambda *args: launched.append(args[0]))
    manager.start('service')
    assert launched == ['service']
    assert (root / 'workspace' / 'proof').read_text() == 'survives abrupt exit'


def test_default_child_has_parent_lifeline_and_private_writable_root(manager, monkeypatch):
    metadata = create_disk(manager, monkeypatch)
    spec = json.loads((manager.config.instances_dir / 'service/bundle/config.json').read_text())
    assert spec['root'].endswith('/service/rootfs')
    assert metadata['filesystem'] == 'cow'
    assert metadata['standalone'] is False
    assert all(source != '/' for source, target in spec['bindings'])


def test_standalone_boots_command_directly_and_manual_stop_prevents_restore(manager, monkeypatch):
    metadata = create_disk(manager, monkeypatch, standalone=True, command=['/bin/sh', '-c', 'sleep 5'])
    spec = json.loads((manager.config.instances_dir / 'service/bundle/config.json').read_text())
    assert spec['command'] == ['/bin/sh', '-c', 'sleep 5']
    monkeypatch.setattr(manager, '_runtime_state', lambda *args: (None, 'container not found'))
    manager.stop('service')
    assert not manager.inspect('service').desired_running
    assert manager.restore_standalone() == []


def test_usr_default_mount_and_explicit_host_root(manager, monkeypatch, tmp_path):
    user = tmp_path / 'usr'
    manager.config = dataclasses.replace(manager.config, user_dir=user)
    metadata = create_disk(manager, monkeypatch)
    assert metadata['mounts'] == [{'source': str(user), 'destination': '/a0/usr', 'read_only': False}]
    with pytest.raises(SandboxError, match='host_root=True'):
        manager.create('unsafe', mounts=[SandboxMount(Path('/'), '/host')])


def test_instance_identity_is_checked_before_runtime_access(manager):
    manager.config=dataclasses.replace(manager.config,instance_id='one')
    metadata=_metadata(manager,'state');metadata['instance_id']='one'
    with pytest.raises(SandboxError,match='another Agent Zero'):
        manager._validated_metadata('state',{**metadata,'instance_id':'two'})


def test_bounded_output_reads_reject_guest_symlinks_and_devices(manager, monkeypatch):
    create_disk(manager, monkeypatch)
    root = manager.config.instances_dir / 'service' / 'rootfs'
    (root / 'workspace' / 'log').write_text('123456789')
    assert manager.read_file('service', 'workspace/log', limit=4) == '6789'
    (root / 'workspace' / 'escape').symlink_to('/etc/passwd')
    with pytest.raises(OSError):
        manager.read_file('service', 'workspace/escape')
    (root / 'escape').symlink_to('/etc', target_is_directory=True)
    with pytest.raises(OSError):
        manager.read_file('service', 'escape/passwd')
    with pytest.raises(SandboxError):
        manager.read_file('service', '../metadata.json')
    os.mkfifo(root / 'workspace' / 'fifo')
    with pytest.raises(SandboxError, match='regular file'):
        manager.read_file('service', 'workspace/fifo')


def test_usr_mount_masks_private_control_files(manager, monkeypatch, tmp_path):
    manager.config = dataclasses.replace(manager.config, user_dir=tmp_path)
    metadata = create_disk(manager, monkeypatch)
    spec = json.loads((manager.config.instances_dir / 'service/bundle/config.json').read_text())
    bindings = {destination: source for source, destination in spec['bindings']}
    assert bindings['/a0/usr/state'] in spec['readonly']
    assert bindings['/a0/usr/images'] in spec['readonly']


def test_parent_lifeline_is_passed_only_for_child_sandboxes(manager, monkeypatch):
    metadata=_metadata(manager,'quick'); metadata['standalone']=False
    seen=[]
    monkeypatch.setattr(manager,'_launch_runtime',lambda name,metadata,fd:seen.append(fd))
    manager._launch('quick',metadata)
    assert isinstance(seen[0],int)
    os.close(manager._child_pipes.pop('quick'))
    metadata['standalone']=True;manager._launch('quick',metadata)
    assert seen[-1] is None


def test_start_reasserts_desired_state_when_runtime_already_exists(manager, monkeypatch):
    metadata = _metadata(manager, 'existing')
    metadata['desired_running'] = False
    manager._atomic_write_json(manager.config.instances_dir / 'existing' / 'metadata.json', metadata)
    monkeypatch.setattr(manager, '_runtime_state', lambda *args: ({'status': 'running'}, None))
    manager.start('existing')
    assert manager.inspect('existing').desired_running
