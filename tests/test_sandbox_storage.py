import asyncio
import dataclasses
import json
import threading

import pytest

from plugins._sandboxing.helpers.manager import SandboxError
from tests.test_sandboxing import IMAGE_DIGEST, manager
from tests.test_sandbox_services import create_disk


def test_lifecycle_and_broken_status_never_measure_storage(manager, monkeypatch):
    monkeypatch.setattr('plugins._sandboxing.helpers.manager.allocated_bytes',
                        lambda *args: pytest.fail('Implicit storage scan'))
    create_disk(manager, monkeypatch)
    assert manager.start('service').size_bytes is None
    assert manager.save('service').size_bytes is None
    assert manager.inspect('service').size_bytes is None
    assert manager.list()[0].size_bytes is None
    monkeypatch.setattr(manager, '_runtime_state', lambda *args: (None, 'container not found'))
    assert manager.stop('service').size_bytes is None
    manager.start('service')
    (manager.config.instances_dir / 'service/metadata.json').write_text('{}')
    assert manager.inspect('service').status == 'broken'
    assert manager.list()[0].size_bytes is None


def test_image_status_uses_only_recorded_size(manager, monkeypatch):
    monkeypatch.setattr(manager.images, '_allocated_bytes',
                        lambda *args: pytest.fail('Implicit image storage scan'))
    assert manager.images.inspect(IMAGE_DIGEST).size_bytes == 0
    path = manager.images.config.cache_dir / IMAGE_DIGEST.replace(':', '-') / 'metadata.json'
    metadata = json.loads(path.read_text())
    metadata.pop('size_bytes')
    path.write_text(json.dumps(metadata))
    assert manager.images.inspect(IMAGE_DIGEST).size_bytes is None
    assert manager.images.list()[0].size_bytes is None
    path.write_text('{}')
    assert manager.images.list()[0].status == 'broken'
    assert manager.images.list()[0].size_bytes is None


def test_explicit_usage_checks_ownership_and_does_not_follow_links(manager, monkeypatch, tmp_path):
    manager.config = dataclasses.replace(manager.config, instance_id='original')
    create_disk(manager, monkeypatch)
    before = manager.disk_usage('service')
    root = manager.config.instances_dir / 'service/rootfs'
    (root / 'data').write_bytes(b'x' * 65536)
    assert manager.disk_usage('service') >= before + 65536
    external = tmp_path / 'external'
    external.mkdir()
    (external / 'large').write_bytes(b'x' * 1048576)
    (root / 'link').symlink_to(external, target_is_directory=True)
    assert manager.disk_usage('service') < before + 1048576
    (manager.config.instances_dir / 'alias').symlink_to(root.parent, target_is_directory=True)
    for name in ('../external', 'alias', 'missing'):
        with pytest.raises(SandboxError):
            manager.disk_usage(name)
    manager.config = dataclasses.replace(manager.config, instance_id='different')
    with pytest.raises(SandboxError, match='another Agent Zero'):
        manager.disk_usage('service')


@pytest.mark.asyncio
async def test_slow_usage_does_not_block_api_status_or_lifecycle(manager, monkeypatch):
    from plugins._sandboxing.api import sandboxes

    create_disk(manager, monkeypatch)
    monkeypatch.setattr(sandboxes, 'get_manager', lambda: manager)
    monkeypatch.setattr(sandboxes, 'defaults', lambda: ('default', 'temporary', 'host'))
    entered, release = threading.Event(), threading.Event()

    def slow_scan(path):
        entered.set()
        assert release.wait(5), 'Test did not release storage calculation'
        return 1234

    monkeypatch.setattr('plugins._sandboxing.helpers.manager.allocated_bytes', slow_scan)
    handler = object.__new__(sandboxes.Sandboxes)
    calculation = asyncio.create_task(handler.process({'action': 'disk_usage', 'name': 'service'}, None))
    try:
        assert await asyncio.to_thread(entered.wait, 2)
        for action in ('list', 'start'):
            result = await asyncio.wait_for(handler.process({'action': action, 'name': 'service'}, None), 1)
            assert result['ok']
        assert not calculation.done()
    finally:
        release.set()
        result = await calculation
    assert result == {'ok': True, 'name': 'service', 'size_bytes': 1234}


def test_cli_measures_only_when_requested(manager, monkeypatch, capsys):
    from helpers import dotenv, sandbox

    create_disk(manager, monkeypatch)
    monkeypatch.setattr(sandbox, 'get_manager', lambda: manager)
    monkeypatch.setattr(dotenv, 'load_dotenv', lambda: None)
    monkeypatch.setattr(manager, 'disk_usage', lambda name: 1234)
    assert sandbox.main(['inspect', 'service']) == 0
    assert json.loads(capsys.readouterr().out)['size_bytes'] is None
    assert sandbox.main(['disk-usage', 'service']) == 0
    assert json.loads(capsys.readouterr().out)['size_bytes'] == 1234
