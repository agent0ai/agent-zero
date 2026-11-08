from types import SimpleNamespace
import sys

import numpy as np
import pytest

from helpers import local_embeddings as local


@pytest.mark.parametrize('provider,name,expected', [
    ('huggingface', local.MODEL, {'cache_folder': '/custom/model cache', 'token': False}),
    ('openai', 'remote-model', {}),
    ('huggingface', 'sentence-transformers/another-model', {}),
])
def test_preparation_uses_only_bundled_model_storage_settings(monkeypatch, provider, name, expected):
    from plugins._model_config.helpers import model_config

    config = SimpleNamespace(provider=provider, name=name, build_kwargs=lambda: {
        'cache_folder': '/custom/model cache', 'use_auth_token': False, 'api_key': 'unused',
    })
    monkeypatch.setattr(model_config, 'get_saved_embedding_model_configs', lambda: [config])
    assert local.configured_asset_options() == [expected]


def test_preparation_resolves_all_saved_presets_with_runtime_inheritance_and_aliases(monkeypatch, tmp_path):
    from plugins._model_config.helpers import model_config

    monkeypatch.setattr(model_config.files, '_base_dir', str(tmp_path))
    presets = [
        {'name': 'Default', 'embedding': {
            'provider': 'huggingface', 'name': local.MODEL,
            'kwargs': {'cache_folder': '/global cache', 'use_auth_token': False},
        }},
        {'name': 'Chat cache', 'embedding': {
            'provider': 'other', 'name': 'huggingface/' + local.MODEL,
            'kwargs': {'cache_folder': '/chat cache', 'use_auth_token': False},
        }},
        {'name': 'Inherited'},
        {'name': 'Cleared kwargs', 'embedding': {'provider': 'huggingface', 'name': 'all-MiniLM-L6-v2'}},
        {'name': 'Remote', 'embedding': {'provider': 'openai', 'name': 'remote'}},
        {'name': 'Unsupported', 'embedding': {'provider': 'huggingface', 'name': 'another-model'}},
    ]
    monkeypatch.setattr(model_config, 'get_presets', lambda: presets)
    monkeypatch.setattr(model_config.plugins, 'get_plugin_config', lambda *a, **k: {'model_preset': 'Default'})
    agent = SimpleNamespace(context=SimpleNamespace(get_data=lambda key: (
        {'preset_name': 'Chat cache'} if key == 'chat_model_override' else None
    )))
    chat = model_config.get_embedding_model_config_object(agent)
    assert chat.name == local.MODEL and chat.provider == 'huggingface'
    assert local.configured_asset_options() == [
        {'cache_folder': '/global cache', 'token': False},
        {'cache_folder': chat.kwargs['cache_folder'], 'token': chat.kwargs['use_auth_token']},
        {'cache_folder': None, 'token': None},
    ]
    # A remote global choice must not hide local models selectable by a chat or scope.
    monkeypatch.setattr(model_config.plugins, 'get_plugin_config', lambda *a, **k: {'model_preset': 'Remote'})
    assert len(local.configured_asset_options()) == 3


def test_preparation_resolves_persisted_raw_chat_override_in_its_scope(monkeypatch, tmp_path):
    import json
    from helpers import files, plugins, projects
    from plugins._model_config.helpers import model_config
    from test_model_config_project_presets import _prepare_a0_tree, _clear_runtime_caches

    _prepare_a0_tree(monkeypatch, tmp_path)
    try:
        default = model_config.get_presets()[0]
        default['embedding'] = {'provider': 'openai', 'name': 'remote'}
        model_config.save_presets([
            default,
            {'name': 'Local', 'embedding': {
                'provider': 'huggingface', 'name': local.MODEL,
                'kwargs': {'cache_folder': '/scope cache'},
            }},
        ])
        plugins.save_plugin_config('_model_config', 'project', 'profile', {'model_preset': 'Local'})
        data = {projects.CONTEXT_DATA_KEY_PROJECT: 'project', 'chat_model_override': {
            'embedding': {'name': 'all-MiniLM-L6-v2', 'kwargs': {
                'cache_folder': '/raw chat cache', 'use_auth_token': False,
            }},
        }}
        path = tmp_path / 'usr/chats/raw/chat.json'
        files.write_file(str(path), json.dumps({'data': data, 'agent_profile': 'other',
                                              'agents': [{'agent_profile': 'profile'}]}))
        before = path.read_bytes()
        # Exercise the ordinary runtime resolver; this stays a raw override on disk.
        agent = SimpleNamespace(config=SimpleNamespace(profile='profile'),
                                context=SimpleNamespace(get_data=data.get))
        resolved = model_config.get_embedding_model_config_object(agent)
        assert resolved.provider == 'huggingface' and resolved.name == local.MODEL
        assert local.configured_asset_options() == [
            {'cache_folder': '/scope cache', 'token': None},
            {'cache_folder': resolved.kwargs['cache_folder'], 'token': False},
        ]
        assert path.read_bytes() == before
        # Invalid chat state is left untouched for the normal loader to report.
        for name, value in [('broken', '{'), ('list', '[]'), ('bad-data', '{"data": []}')]:
            files.write_file(f'usr/chats/{name}/chat.json', value)
        assert len(local.configured_asset_options()) == 2
    finally:
        _clear_runtime_caches()


@pytest.mark.parametrize('model,kwargs', [
    ('another-model', {}), (local.MODEL, {'revision': 'main'}),
    (local.MODEL, {'device': 'cuda'}), (local.MODEL, {'trust_remote_code': True}),
    (local.MODEL, {'model_kwargs': {'torch_dtype': 'float16'}}),
])
def test_unvalidated_configuration_fails_before_asset_or_index_access(monkeypatch, model, kwargs):
    monkeypatch.setattr(local, 'model_assets', lambda **_: pytest.fail('Asset access'))
    with pytest.raises(ValueError):
        local.OnnxSentenceTransformer(model, **kwargs)


def test_assets_are_revision_pinned_offline_and_hash_checked(monkeypatch, tmp_path):
    p = tmp_path/'model'; p.write_bytes(b'fixture')
    import hashlib
    monkeypatch.setattr(local, 'ASSETS', {'fixture': hashlib.sha256(b'fixture').hexdigest()})
    calls = []
    def download(*args, **kwargs):
        calls.append((args, kwargs))
        return str(p)
    monkeypatch.setitem(sys.modules, 'huggingface_hub', SimpleNamespace(hf_hub_download=download))
    assert local.model_assets(cache_folder='cache') == {'fixture': p}
    assert calls[0] == ((local.MODEL, 'fixture'), {'revision': local.REVISION,
                       'cache_dir': 'cache', 'token': None, 'local_files_only': True})
    p.write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='checksum'):
        local.model_assets()


def test_pooling_masks_padding_normalizes_and_bounds_batches():
    lengths = []
    class Tokenizer:
        def encode_batch(self, inputs):
            lengths.append(len(inputs))
            return [SimpleNamespace(ids=[int(x), 0], attention_mask=[1, 0], type_ids=[0, 0]) for x in inputs]
    class Session:
        def run(self, names, feed):
            assert names == ['last_hidden_state']
            assert all(x.dtype == np.int64 for x in feed.values())
            return [np.array([[[n, 1], [999, 999]] for n in feed['input_ids'][:,0]], dtype=np.float32)]
    encoder = local.OnnxSentenceTransformer.__new__(local.OnnxSentenceTransformer)
    encoder.np, encoder.session, encoder.tokenizer = np, Session(), Tokenizer()
    vectors = encoder.encode([str(x) for x in range(35)])
    assert lengths == [32, 3]
    expected = np.array([[x, 1] for x in range(35)], dtype=np.float32)
    expected /= np.linalg.norm(expected, axis=1, keepdims=True)
    np.testing.assert_allclose(vectors, expected, atol=1e-7)
    assert vectors.dtype == np.float32
    assert encoder.encode([]).shape == (0, 384)
    with pytest.raises(TypeError): encoder.encode([None])
    with pytest.raises(ValueError): encoder.encode(['1'], convert_to_tensor=True)
