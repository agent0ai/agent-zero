import asyncio
import base64
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest
import soundfile as sf

from helpers import cache, files, plugins
from plugins._kokoro_tts import hooks
from plugins._kokoro_tts.api.status import Status
from plugins._kokoro_tts.extensions.python.startup_migration import _20_tts_dependencies as startup
from plugins._kokoro_tts.extensions.python._functions.helpers.plugins.toggle_plugin.end import _20_tts_dependencies as enable
from plugins._kokoro_tts.helpers import migration, paradee, runtime

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dependency_hooks_leave_host_environment_untouched(monkeypatch):
    monkeypatch.setattr(subprocess, 'check_call', lambda *args, **kwargs: pytest.fail('Host installation'))
    assert hooks.install()
    assert hooks.ensure_dependencies()
    requirements = (PROJECT_ROOT / 'plugins/_kokoro_tts/sandbox/requirements.txt').read_text()
    assert 'onnxruntime' in requirements and 'en-core-web-sm' in requirements


def test_startup_and_reenable_call_the_plugin_hook(monkeypatch):
    calls = []
    call = lambda *args, **kwargs: calls.append((args, kwargs))
    monkeypatch.setattr(startup, "call_plugin_hook", call)
    monkeypatch.setattr(enable, "call_plugin_hook", call)
    startup.LocalTtsDependencies(None).execute()
    extension = enable.LocalTtsEnabled(None)
    extension.execute(data={"args": ("_kokoro_tts", True), "kwargs": {}, "exception": None})
    extension.execute(data={"args": (), "kwargs": {"plugin_name": "_kokoro_tts", "enabled": True}, "exception": None})
    extension.execute(data={"args": ("_kokoro_tts", False), "kwargs": {}, "exception": None})
    extension.execute(data={"args": ("_other", True), "kwargs": {}, "exception": None})
    extension.execute(data={"args": ("_kokoro_tts", True), "kwargs": {}, "exception": RuntimeError()})
    assert calls == [(("_kokoro_tts", "ensure_dependencies"), {"raise_on_error": False})] * 3


@pytest.mark.parametrize("config,voice,weights", [
    ({}, "paradee", {}),
    ({"voice": ""}, "paradee", {}),
    ({"voice": " Paradee "}, "paradee", {}),
    ({"voice": "paradee", "voice_weights": {"am_puck": 2}}, "am_puck", {"am_puck": 2.0}),
    ({"voice": "paradee,am_puck"}, "am_puck", {}),
    ({"voice": "paradee,custom/voice.pt"}, "custom/voice.pt", {}),
    ({"voice_weights": {"paradee": 1}}, "paradee", {}),
    ({"voice": "am_puck,am_onyx"}, "am_puck,am_onyx", {}),
])
def test_voice_selection_preserves_kokoro_blends(config, voice, weights):
    normalized = runtime.normalize_config({**config, "speed": 1.4})
    assert normalized == {"voice": voice, "voice_weights": weights, "speed": 1.4}


def test_saved_kokoro_voice_and_global_toggle_are_preserved(monkeypatch, tmp_path):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(cache, "_cache", {})
    monkeypatch.setattr(migration, "LEGACY_SETTINGS_FILE", str(tmp_path / "usr/settings.json"))
    (tmp_path / "usr/plugins").mkdir(parents=True)
    bundled = tmp_path / "plugins/_kokoro_tts"
    bundled.mkdir(parents=True)
    for name in ("plugin.yaml", "default_config.yaml", "hooks.py"):
        shutil.copyfile(PROJECT_ROOT / "plugins/_kokoro_tts" / name, bundled / name)
    assert runtime.get_config()["voice"] == "paradee"
    assert runtime.is_globally_enabled()
    saved = tmp_path / "usr/plugins/_kokoro_tts"
    saved.mkdir(parents=True)
    config = {"voice": "am_puck,am_onyx", "voice_weights": {"am_puck": 3, "am_onyx": 1}, "speed": 1.6}
    (saved / "config.json").write_text(json.dumps(config))
    (saved / ".toggle-0").touch()
    assert runtime.get_config() == config
    assert not runtime.is_globally_enabled()


def test_paradee_dispatch_and_status_use_guest_engine(monkeypatch):
    calls = []
    async def call(payload, **kwargs):
        calls.append(payload)
        return {'audio': 'audio', 'version': '1.19.2'}
    monkeypatch.setattr(runtime.worker, 'acall', call)
    monkeypatch.setattr(runtime.worker, 'ready', True)
    monkeypatch.setattr(runtime, '_loaded_engines', set())
    result = asyncio.run(runtime.synthesize_sentences(['Hello', 'World'], {'voice': 'paradee', 'speed': 1.4}))
    assert result == 'audio'
    assert calls[0]['config']['voice'] == 'paradee'
    assert calls[0]['sentences'] == ['Hello', 'World']
    assert asyncio.run(runtime.is_downloaded({'voice': 'paradee'}))
    assert not asyncio.run(runtime.is_downloaded({'voice': 'af_heart'}))
    monkeypatch.setattr(runtime.worker, 'ready', False)
    assert not asyncio.run(runtime.is_downloaded({'voice': 'paradee'}))


def test_phoneme_chunks_keep_all_long_input():
    for text in ("a" * 1200, "hello " * 300, "hello.\nworld!"):
        chunks = list(paradee._phoneme_chunks(text, lambda s: (s, None)))
        assert all(0 < len(chunk) <= 510 for chunk in chunks)
        assert "".join(chunks).replace(" ", "") == text.replace(" ", "").replace("\n", "")


def test_synthesis_produces_wav_and_forwards_speed(monkeypatch):
    feeds = []

    class Session:
        def run(self, _, feed):
            feeds.append(feed)
            return [np.full((1, 2400), 0.1, dtype=np.float32)]

    monkeypatch.setattr(paradee, "_load_model", lambda: (Session(), lambda s: (s, None), {"a": 1}))
    audio = paradee.synthesize("a" * 1200, 1.4)
    wave, rate = sf.read(io.BytesIO(base64.b64decode(audio)))
    assert rate == 24000 and len(wave) == 7200
    for feed in feeds:
        ids = feed["input_ids"]
        assert ids.shape[1] <= 512 and ids.dtype == np.int64
        assert ids[0, 0] == ids[0, -1] == 0
        assert feed["speed"][0] == pytest.approx(1.4)
    with pytest.raises(ValueError, match="no speakable"):
        paradee.synthesize("🙂", 1.0)


def test_missing_phonemizer_never_installs_packages(monkeypatch):
    spacy = pytest.importorskip("spacy")

    monkeypatch.setattr(spacy.util, "is_package", lambda name: False)
    monkeypatch.setattr(spacy.cli, "download", lambda *args: pytest.fail("Runtime package installation"))
    with pytest.raises(RuntimeError, match="phonemizer model is missing"):
        paradee._initialize_model()


def test_failed_load_resets_loading_status(monkeypatch):
    monkeypatch.setattr(paradee, "_model", None)

    def fail():
        raise RuntimeError("Model failed")

    monkeypatch.setattr(paradee, "_initialize_model", fail)
    with pytest.raises(RuntimeError, match="Model failed"):
        paradee.preload()
    assert paradee.model_status() == {"ready": False, "loading": False}


def test_voice_picker_switches_models_without_cross_model_blends():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js unavailable")
    html = (PROJECT_ROOT / "plugins/_kokoro_tts/webui/config.html").read_text()
    component = html.split('<div x-data="', 1)[1].split('">', 1)[0]
    script = "const config = {voice:'am_puck', voice_weights:{am_puck:3}, speed:1.4};\n"
    script += "const ui = (" + component + ");\n"
    script += """
      const assert = (value) => { if (!value) throw new Error('Voice picker assertion'); };
      ui.initConfig();
      ui.addVoice('paradee');
      assert(config.voice === 'paradee' && !ui.hasWeights());
      assert(ui.voiceIds().join(',') === 'paradee');
      ui.setWeight('paradee', 2);
      assert(!ui.hasWeights());
      ui.addVoice('am_onyx');
      assert(config.voice === 'am_onyx' && !ui.hasWeights());
      ui.addVoice('am_puck');
      ui.setWeight('am_puck', 3);
      assert(config.voice === 'am_onyx,am_puck' && config.voice_weights.am_puck === 3);
      ui.addVoice('paradee');
      assert(config.voice === 'paradee' && !ui.hasWeights() && config.speed === 1.4);
    """
    subprocess.run([node, "-"], input=script, text=True, check=True, capture_output=True)
