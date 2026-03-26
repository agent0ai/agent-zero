import sys
import threading
import types
from pathlib import Path

from flask import Flask


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.modules["giturlparse"] = types.SimpleNamespace(parse=lambda *args, **kwargs: None)


class _DummyObserver:
    def __init__(self):
        self._alive = False

    def is_alive(self):
        return self._alive

    def start(self):
        self._alive = True

    def stop(self):
        self._alive = False

    def join(self, *args, **kwargs):
        return None

    def unschedule_all(self):
        return None

    def schedule(self, *args, **kwargs):
        return None


watchdog = types.ModuleType("watchdog")
watchdog.observers = types.SimpleNamespace(Observer=_DummyObserver)
watchdog.events = types.SimpleNamespace(FileSystemEventHandler=object)
sys.modules["watchdog"] = watchdog
sys.modules["watchdog.observers"] = watchdog.observers
sys.modules["watchdog.events"] = watchdog.events

from plugins._model_config.api.api_keys import ApiKeys
import models


def test_model_config_api_keys_can_be_cleared_via_backend(monkeypatch, tmp_path):
    from helpers import dotenv

    env_file = tmp_path / ".env"
    monkeypatch.setattr(dotenv, "get_dotenv_file_path", lambda: str(env_file))

    for key in ("API_KEY_OPENROUTER", "OPENROUTER_API_KEY", "OPENROUTER_API_TOKEN"):
        monkeypatch.delenv(key, raising=False)

    handler = ApiKeys(Flask(__name__), threading.Lock())

    assert handler._set_keys({"keys": {"openrouter": "sk-test-openrouter"}}) == {"ok": True}
    assert models.get_api_key("openrouter") == "sk-test-openrouter"

    assert handler._set_keys({"keys": {"openrouter": ""}}) == {"ok": True}
    assert models.get_api_key("openrouter") == "None"
    assert handler._reveal_key({"provider": "openrouter"}) == {"ok": True, "value": ""}


def test_model_config_frontend_tracks_inline_api_key_edits():
    store_path = PROJECT_ROOT / "plugins" / "_model_config" / "webui" / "model-config-store.js"
    config_path = PROJECT_ROOT / "plugins" / "_model_config" / "webui" / "config.html"
    modal_path = PROJECT_ROOT / "plugins" / "_model_config" / "webui" / "api-keys.html"

    store_content = store_path.read_text(encoding="utf-8")
    config_content = config_path.read_text(encoding="utf-8")
    modal_content = modal_path.read_text(encoding="utf-8")

    assert "apiKeyDirty" in store_content
    assert "resetApiKeyDrafts()" in store_content
    assert "!provider || seen.has(provider) || !this.apiKeyDirty[provider]" in store_content
    assert "normalized[provider] = value.trim() ? value : '';" in store_content
    assert "$store.modelConfig.resetApiKeyDrafts();" in config_content
    assert '@input="$store.modelConfig.touchApiKey(config[section.key].provider)"' in config_content
    assert "updates[provider] = this.keys[provider] || '';" in modal_content
    assert "$store.modelConfig.resetApiKeyDrafts();" in modal_content
