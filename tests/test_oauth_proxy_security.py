import copy
from pathlib import Path

import pytest
import yaml
from flask import Flask

import models
from helpers import extension, runtime
from plugins._model_config.helpers import model_config
from plugins._oauth.extensions.python._functions.models._merge_provider_defaults.end import (
    _20_oauth_proxy_key as oauth_proxy_key,
)
from plugins._oauth.extensions.python._functions.models.get_api_key.end import (
    _20_oauth_account_dummy_key as oauth_key,
)
from plugins._oauth.helpers import config, routes
from plugins._oauth.helpers.providers import CODEX_PROVIDER_ID, get_provider, oauth_provider_ids


@pytest.fixture(autouse=True)
def isolate_oauth_model_extensions(monkeypatch):
    hooks = {
        "_functions/models/get_api_key/end": [oauth_key.OAuthAccountDummyKey],
        "_functions/models/_merge_provider_defaults/end": [oauth_proxy_key.OAuthProxyKey],
    }
    monkeypatch.setattr(extension, "_get_extension_classes", lambda point, **kwargs: hooks.get(point, []))
    monkeypatch.setattr(oauth_key, "oauth_provider_is_connected", lambda _: True)
    monkeypatch.setattr(models, "get_api_key_raw", lambda _: "None")
    monkeypatch.setattr(config, "oauth_config", lambda: {})
    monkeypatch.setattr(runtime, "get_web_ui_port", lambda: 80)
    providers = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "plugins/_oauth/conf/model_providers.yaml").read_text()
    )
    monkeypatch.setattr(models, "get_provider_config", lambda kind, provider: providers.get(kind, {}).get(provider))


def _proxy_app(monkeypatch, *, proxy_token=""):
    monkeypatch.setattr(
        routes,
        "codex_config",
        lambda: {
            "proxy_base_path": "/oauth/codex",
            "callback_path": "/auth/callback",
            "proxy_token": proxy_token,
            "require_proxy_token": False,
        },
    )
    monkeypatch.setattr(routes, "provider_registry", lambda: {})
    app = Flask(__name__)
    routes.register_oauth_routes(app)
    return app


def test_tokenless_loopback_request_cannot_use_account_proxy(monkeypatch):
    upstream_calls = []
    monkeypatch.setattr(routes.codex, "fetch_models", lambda: upstream_calls.append(True) or [])
    app = _proxy_app(monkeypatch)

    response = app.test_client().get(
        "/oauth/codex/v1/models",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "access_denied"
    assert upstream_calls == []


def test_internal_model_credential_authorizes_account_proxy(monkeypatch):
    monkeypatch.setattr(routes.codex, "fetch_models", lambda: ["synthetic-model"])
    app = _proxy_app(monkeypatch)
    model_key = {"args": (CODEX_PROVIDER_ID,), "kwargs": {}, "result": "None"}
    oauth_key.OAuthAccountDummyKey(agent=None).execute(data=model_key)

    response = app.test_client().get(
        "/oauth/codex/v1/models",
        headers={"Authorization": f"Bearer {model_key['result']}"},
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"][0]["id"] == "synthetic-model"


def test_connected_model_replaces_legacy_stored_key_with_internal_credential(monkeypatch):
    monkeypatch.setattr(routes.codex, "fetch_models", lambda: ["synthetic-model"])
    monkeypatch.setattr(models, "get_api_key_raw", lambda _: "legacy-stored-key")
    app = _proxy_app(monkeypatch)

    model_key = models.get_api_key(CODEX_PROVIDER_ID)
    response = app.test_client().get(
        "/oauth/codex/v1/models",
        headers={"Authorization": f"Bearer {model_key}"},
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
    )

    assert model_key == oauth_key.DUMMY_API_KEY
    assert response.status_code == 200


@pytest.mark.parametrize("provider_id", sorted(oauth_provider_ids()))
@pytest.mark.parametrize("key_location", ["automatic", "inline", "kwargs", "headers"])
@pytest.mark.parametrize("connected", [False, True])
def test_local_oauth_models_authenticate_without_changing_saved_settings(
    monkeypatch, provider_id, key_location, connected
):
    monkeypatch.setattr(oauth_key, "oauth_provider_is_connected", lambda _: connected)
    slot = {"provider": provider_id, "name": "synthetic-model"}
    if key_location == "inline":
        slot["api_key"] = "oauth"
    elif key_location == "kwargs":
        slot["kwargs"] = {"api_key": "legacy-stored-key"}
    elif key_location == "headers":
        slot["kwargs"] = {
            "extra_headers": {"authorization": "Bearer oauth", "X-API-Key": "oauth", "session-id": "keep"}
        }
    original_slot = copy.deepcopy(slot)
    mc = model_config.build_model_config(slot, models.ModelType.CHAT)

    model = models.get_chat_model(mc.provider, mc.name, model_config=mc, **mc.build_kwargs())
    app = _proxy_app(monkeypatch)
    with app.test_request_context(headers={"Authorization": f"Bearer {model.kwargs['api_key']}"}):
        assert routes._proxy_authorized()
    assert slot == original_slot
    if key_location == "headers":
        assert model.kwargs["extra_headers"] == {"session-id": "keep"}


@pytest.mark.parametrize("provider_id", sorted(oauth_provider_ids()))
@pytest.mark.parametrize("api_base", [
    "https://external.invalid/v1",
    "http://localhost:8081{proxy_path}/v1",
    "http://localhost/external/v1",
])
def test_external_oauth_model_endpoint_preserves_explicit_credentials(provider_id, api_base):
    model = models.get_chat_model(
        provider_id, "synthetic-model",
        api_base=api_base.format(proxy_path=get_provider(provider_id).metadata().proxy_base_path),
        api_key="external-token",
        extra_headers={"Authorization": "Bearer external-token"},
    )

    assert model.kwargs["api_key"] == "external-token"
    assert model.kwargs["extra_headers"]["Authorization"] == "Bearer external-token"


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "[::1]"])
def test_internal_proxy_authentication_follows_the_web_ui_port(monkeypatch, host):
    monkeypatch.setattr(runtime, "get_web_ui_port", lambda: 50001)
    model = models.get_chat_model(
        CODEX_PROVIDER_ID, "synthetic-model",
        api_base=f"http://{host}:50001/oauth/codex/v1", api_key="oauth",
    )

    assert model.kwargs["api_key"] == oauth_key.DUMMY_API_KEY


def test_explicit_proxy_token_remains_supported(monkeypatch):
    monkeypatch.setattr(routes.codex, "fetch_models", lambda: ["synthetic-model"])
    app = _proxy_app(monkeypatch, proxy_token="configured-proxy-token")

    response = app.test_client().get(
        "/oauth/codex/v1/models",
        headers={"X-API-Key": "configured-proxy-token"},
        environ_overrides={"REMOTE_ADDR": "203.0.113.10"},
    )

    assert response.status_code == 200
