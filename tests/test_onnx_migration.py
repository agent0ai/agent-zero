from unittest.mock import Mock
import hashlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from huggingface_hub.errors import LocalEntryNotFoundError
from extensions.python.startup_migration import _21_onnx_embeddings as migration
from helpers import local_embeddings


@pytest.fixture(autouse=True)
def default_asset_options(monkeypatch):
    original = local_embeddings.configured_asset_options
    monkeypatch.setattr(local_embeddings, 'configured_asset_options', lambda: [{}])
    return original


def test_upgrade_prepares_missing_assets_before_returning(monkeypatch):
    monkeypatch.setattr(migration.runtime, 'is_dockerized', lambda: True)
    assets = Mock(side_effect=[LocalEntryNotFoundError('missing'), {}])
    monkeypatch.setattr(local_embeddings, 'model_assets', assets)
    run = Mock()
    monkeypatch.setattr(migration.subprocess, 'run', run)
    migration.OnnxEmbeddings(None).execute()
    assert assets.call_count == 2
    command = run.call_args.args[0]
    assert command[0] == migration.sys.executable
    assert command[1:] == ['-m', 'helpers.local_embeddings']
    assert run.call_args.kwargs == {'cwd': migration.files.get_base_dir(), 'check': True, 'timeout': 180}


def test_ready_image_skips_upgrade_process(monkeypatch):
    monkeypatch.setattr(migration.runtime, 'is_dockerized', lambda: True)
    monkeypatch.setattr(local_embeddings, 'model_assets', lambda: {})
    monkeypatch.setattr(migration.subprocess, 'run', lambda *a, **k: pytest.fail('Unexpected process'))
    migration.OnnxEmbeddings(None).execute()


def test_corrupt_assets_stop_startup_without_uninstalling_anything(monkeypatch):
    monkeypatch.setattr(migration.runtime, 'is_dockerized', lambda: True)
    monkeypatch.setattr(local_embeddings, 'model_assets', Mock(side_effect=ValueError('checksum')))
    monkeypatch.setattr(migration.subprocess, 'run', lambda *a, **k: pytest.fail('Unexpected process'))
    with pytest.raises(ValueError, match='checksum'):
        migration.OnnxEmbeddings(None).execute()


def test_failed_preparation_blocks_startup(monkeypatch):
    monkeypatch.setattr(migration.runtime, 'is_dockerized', lambda: True)
    monkeypatch.setattr(local_embeddings, 'model_assets', Mock(side_effect=LocalEntryNotFoundError('missing')))
    monkeypatch.setattr(migration.subprocess, 'run', Mock(side_effect=RuntimeError('download failed')))
    with pytest.raises(RuntimeError, match='download failed'):
        migration.OnnxEmbeddings(None).execute()


def test_upgrade_checks_configured_cache_before_and_after_preparation(monkeypatch):
    monkeypatch.setattr(migration.runtime, 'is_dockerized', lambda: True)
    options = {'cache_folder': '/custom/model cache', 'token': False}
    monkeypatch.setattr(local_embeddings, 'configured_asset_options', lambda: [options])
    assets = Mock(side_effect=[LocalEntryNotFoundError('missing'), {}])
    monkeypatch.setattr(local_embeddings, 'model_assets', assets)
    run = Mock()
    monkeypatch.setattr(migration.subprocess, 'run', run)
    migration.OnnxEmbeddings(None).execute()
    assert [call.kwargs for call in assets.call_args_list] == [options, options]
    assert run.call_count == 1


def test_local_startup_leaves_explicit_preparation_to_setup(monkeypatch):
    monkeypatch.setattr(migration.runtime, 'is_dockerized', lambda: False)
    monkeypatch.setattr(local_embeddings, 'configured_asset_options', lambda: pytest.fail('Unexpected setup'))
    migration.OnnxEmbeddings(None).execute()


def test_upgrade_preserves_and_prepares_global_and_chat_caches(monkeypatch, tmp_path):
    import huggingface_hub

    caches = [tmp_path / 'global cache', tmp_path / 'chat cache']
    for cache in caches:
        cache.mkdir()
        (cache / 'model.safetensors').write_bytes(b'previous weights')
    options = [{'cache_folder': str(cache), 'token': False} for cache in caches]
    monkeypatch.setattr(migration.runtime, 'is_dockerized', lambda: True)
    monkeypatch.setattr(local_embeddings, 'configured_asset_options', lambda: options)
    payload = b'pinned ONNX fixture'
    monkeypatch.setattr(local_embeddings, 'ASSETS', {'model.onnx': hashlib.sha256(payload).hexdigest()})
    downloads = []

    def download(model, name, **kwargs):
        assert model == local_embeddings.MODEL
        cache = Path(kwargs['cache_dir'])
        assert cache in caches and kwargs['token'] is False
        assert kwargs['revision'] == local_embeddings.REVISION
        path = cache / name
        if not path.exists():
            if kwargs['local_files_only']:
                raise LocalEntryNotFoundError('old assets only')
            downloads.append((cache, name))
            path.write_bytes(payload)
        return str(path)

    monkeypatch.setattr(huggingface_hub, 'hf_hub_download', download)
    encoder = Mock(return_value=SimpleNamespace(encode=lambda texts: np.ones((1, 384))))
    monkeypatch.setattr(local_embeddings, 'OnnxSentenceTransformer', encoder)
    run = Mock(side_effect=lambda *args, **kwargs: local_embeddings.prepare_model())
    monkeypatch.setattr(migration.subprocess, 'run', run)
    migration.OnnxEmbeddings(None).execute()
    migration.OnnxEmbeddings(None).execute()
    assert downloads == [(cache, 'model.onnx') for cache in caches] and run.call_count == 1
    for cache in caches:
        assert (cache / 'model.safetensors').read_bytes() == b'previous weights'
    assert [call.kwargs for call in encoder.call_args_list] == [
        {'cache_folder': str(cache), 'use_auth_token': False} for cache in caches
    ]


def test_upgrade_rechecks_all_caches_after_preparation(monkeypatch):
    monkeypatch.setattr(migration.runtime, 'is_dockerized', lambda: True)
    options = [{'cache_folder': '/global'}, {'cache_folder': '/chat'}]
    monkeypatch.setattr(local_embeddings, 'configured_asset_options', lambda: options)
    assets = Mock(side_effect=[{}, LocalEntryNotFoundError('chat missing'),
                               {}, LocalEntryNotFoundError('chat still missing')])
    monkeypatch.setattr(local_embeddings, 'model_assets', assets)
    run = Mock()
    monkeypatch.setattr(migration.subprocess, 'run', run)
    with pytest.raises(LocalEntryNotFoundError, match='still missing'):
        migration.OnnxEmbeddings(None).execute()
    assert [call.kwargs for call in assets.call_args_list] == options * 2
    assert run.call_count == 1


def test_startup_prepares_legacy_scope_after_config_migration(monkeypatch, tmp_path, default_asset_options):
    import json
    from helpers import extension, files, plugins, projects, subagents
    from plugins._model_config.helpers import model_config
    from plugins._model_config.extensions.python.startup_migration._10_migrate_model_config import MigrateModelConfig
    from plugins._model_config.extensions.python.startup_migration._20_bootstrap_model_presets import BootstrapModelPresets
    from test_model_config_project_presets import _prepare_a0_tree, _clear_runtime_caches

    _prepare_a0_tree(monkeypatch, tmp_path)
    try:
        cache = tmp_path / 'old project cache'
        cache.mkdir()
        (cache / 'model.safetensors').write_bytes(b'old weights')
        config_path = plugins.determine_plugin_asset_path('_model_config', 'project', '', plugins.CONFIG_FILE_NAME)
        original = json.dumps({'embedding_model': {'provider': 'huggingface', 'name': local_embeddings.MODEL,
                                                  'kwargs': {'cache_folder': str(cache)}}})
        files.write_file(config_path, original)
        monkeypatch.setattr(local_embeddings, 'configured_asset_options', default_asset_options)
        monkeypatch.setattr(migration.runtime, 'is_dockerized', lambda: True)

        def assets(**options):
            assert options['cache_folder'] == str(cache)
            if not (cache / 'model.onnx').exists():
                raise LocalEntryNotFoundError('old cache only')

        def prepare(*args, **kwargs):
            assert local_embeddings.configured_asset_options() == [{'cache_folder': str(cache), 'token': None}]
            (cache / 'model.onnx').write_bytes(b'new graph')

        monkeypatch.setattr(local_embeddings, 'model_assets', assets)
        run = Mock(side_effect=prepare)
        monkeypatch.setattr(migration.subprocess, 'run', run)
        monkeypatch.setattr(BootstrapModelPresets, '_download_presets', lambda self: pytest.fail('Already migrated'))
        # Use the real discovery ordering/dispatcher with only the relevant hooks.
        monkeypatch.setattr(subagents, 'get_paths', lambda agent, *parts: (
            ['core', 'model'] if parts == ('extensions/python', 'startup_migration') else []
        ))
        monkeypatch.setattr(extension, '_get_extensions', lambda path: {
            'core': [migration.OnnxEmbeddings],
            'model': [BootstrapModelPresets, MigrateModelConfig],
        }[path])
        extension.call_extensions_sync('startup_migration')
        extension.call_extensions_sync('startup_migration')
        agent = SimpleNamespace(config=SimpleNamespace(profile=''), context=SimpleNamespace(
            get_data={projects.CONTEXT_DATA_KEY_PROJECT: 'project'}.get))
        resolved = model_config.get_embedding_model_config_object(agent)
        assert resolved.kwargs['cache_folder'] == str(cache)
        assert run.call_count == 1 and (cache / 'model.onnx').exists()
        assert (cache / 'model.safetensors').read_bytes() == b'old weights'
        assert Path(config_path + MigrateModelConfig.BACKUP_SUFFIX).read_text() == original
    finally:
        _clear_runtime_caches()
