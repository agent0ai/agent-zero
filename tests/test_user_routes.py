import threading

from flask import Flask

from helpers import cache, files, login, plugins, subagents
from helpers.api import CACHE_AREA, register_api_route
from helpers.extension import get_webui_extension_manifest
from helpers.ui_server import UiServerRuntime


WEBUI_MANIFEST_CACHE_AREA = "webui_extension_manifest(extensions)(plugins)"


def _new_app(name: str) -> Flask:
    app = Flask(name, static_folder=None)
    app.secret_key = "test-secret"
    return app


def _api_handler_source(source: str) -> str:
    return f"""from helpers.api import ApiHandler


class Handler(ApiHandler):
    @classmethod
    def get_methods(cls):
        return ["GET"]

    async def process(self, input, request):
        return {{"source": {source!r}}}
"""


def test_http_dispatches_contained_user_api_handler(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    user_api_dir = tmp_path / "usr" / "api"
    user_api_dir.mkdir(parents=True)
    handler_source = _api_handler_source("user")
    (user_api_dir / "ping.py").write_text(handler_source, encoding="utf-8")
    (tmp_path / "usr" / "escaped.py").write_text(
        handler_source, encoding="utf-8"
    )
    monkeypatch.setattr(login, "get_credentials_hash", lambda: "credential-hash")

    cache.clear(CACHE_AREA)
    try:
        app = _new_app("test_user_api_route")
        app.add_url_rule("/", "serve_index", lambda: "")
        app.add_url_rule("/login", "login_handler", lambda: "")
        register_api_route(app, threading.RLock())
        client = app.test_client()

        assert client.get("/api/ping").status_code == 302
        with client.session_transaction() as session:
            session["authentication"] = "credential-hash"
            session["csrf_token"] = "csrf-token"
        response = client.get("/api/ping", headers={"X-CSRF-Token": "csrf-token"})
        assert response.status_code == 200
        assert response.get_json() == {"source": "user"}

        with app.test_request_context("/api/../escaped", method="GET"):
            denied = app.ensure_sync(app.view_functions["api_dispatch"])("../escaped")
        assert denied.status_code == 404
    finally:
        cache.clear(CACHE_AREA)


def test_existing_api_sources_keep_precedence(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(login, "get_credentials_hash", lambda: "credential-hash")

    builtin_file = tmp_path / "api" / "shared.py"
    builtin_file.parent.mkdir(parents=True)
    builtin_file.write_text(_api_handler_source("builtin"), encoding="utf-8")

    user_api_dir = tmp_path / "usr" / "api"
    (user_api_dir / "plugins" / "demo").mkdir(parents=True)
    (user_api_dir / "shared.py").write_text(
        _api_handler_source("user"), encoding="utf-8"
    )
    (user_api_dir / "plugins" / "demo" / "ping.py").write_text(
        _api_handler_source("user"), encoding="utf-8"
    )

    plugin_dir = tmp_path / "plugins" / "demo"
    (plugin_dir / "api").mkdir(parents=True)
    (plugin_dir / "api" / "ping.py").write_text(
        _api_handler_source("plugin"), encoding="utf-8"
    )
    monkeypatch.setattr(
        plugins,
        "find_plugin_dir",
        lambda name: str(plugin_dir) if name == "demo" else None,
    )

    cache.clear(CACHE_AREA)
    try:
        app = _new_app("test_existing_api_precedence")
        app.add_url_rule("/", "serve_index", lambda: "")
        app.add_url_rule("/login", "login_handler", lambda: "")
        register_api_route(app, threading.RLock())
        client = app.test_client()
        with client.session_transaction() as session:
            session["authentication"] = "credential-hash"
            session["csrf_token"] = "csrf-token"
        headers = {"X-CSRF-Token": "csrf-token"}

        assert client.get("/api/shared", headers=headers).get_json() == {
            "source": "builtin"
        }
        assert client.get("/api/plugins/demo/ping", headers=headers).get_json() == {
            "source": "plugin"
        }
    finally:
        cache.clear(CACHE_AREA)


def test_user_webui_manifest_asset_is_served_from_its_declared_url(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    extension_root = tmp_path / "usr" / "extensions" / "webui"
    extension_file = extension_root / "route-probe" / "probe.js"
    extension_file.parent.mkdir(parents=True)
    extension_file.write_text("export default true;", encoding="utf-8")
    builtin_extension_file = (
        tmp_path / "extensions" / "webui" / "route-probe" / "probe.js"
    )
    builtin_extension_file.parent.mkdir(parents=True)
    builtin_extension_file.write_text("export default false;", encoding="utf-8")
    (extension_root.parent / "escaped.js").write_text("secret", encoding="utf-8")
    monkeypatch.setattr(subagents, "get_paths", lambda *_args, **_kwargs: [str(extension_root)])

    cache.clear(WEBUI_MANIFEST_CACHE_AREA)
    try:
        manifest = get_webui_extension_manifest(agent=None)
        asset_url = manifest["js"]["route-probe"][0]
        assert asset_url == "/usr/extensions/webui/route-probe/probe.js"

        app = _new_app("test_user_webui_extension_route")
        runtime = UiServerRuntime(
            app, None, None, threading.RLock(), {}  # type: ignore[arg-type]
        )
        runtime.register_http_routes()

        client = app.test_client()
        monkeypatch.setattr(login, "get_credentials_hash", lambda: "credential-hash")
        assert client.get(asset_url).status_code == 302

        monkeypatch.setattr(login, "get_credentials_hash", lambda: None)
        builtin_response = client.get("/extensions/webui/route-probe/probe.js")
        assert builtin_response.status_code == 200
        assert builtin_response.get_data(as_text=True) == "export default false;"

        response = client.get(asset_url)
        assert response.status_code == 200
        assert response.get_data(as_text=True) == "export default true;"

        with app.test_request_context("/usr/extensions/webui/../escaped.js"):
            denied = app.ensure_sync(
                app.view_functions["serve_user_extension_asset"]
            )("../escaped.js")
        assert denied.status_code == 403
    finally:
        cache.clear(WEBUI_MANIFEST_CACHE_AREA)
