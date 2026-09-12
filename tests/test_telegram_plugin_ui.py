import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import yaml

from plugins._telegram_integration.api import status as status_api
from plugins._telegram_integration.helpers import bot_manager


ROOT = Path(__file__).parents[1] / "plugins" / "_telegram_integration"


def test_telegram_plugin_exposes_scoped_open_and_config_pages(monkeypatch):
    manifest = yaml.safe_load((ROOT / "plugin.yaml").read_text())
    config = (ROOT / "webui" / "config.html").read_text()
    main = (ROOT / "webui" / "main.html").read_text()

    assert manifest["per_project_config"] is True
    assert manifest["per_agent_config"] is True
    assert "settings-advanced-section" in config
    assert 'class="tg-advanced"' not in config
    assert ".tg-advanced" not in config
    assert "telegram-main-store.js" in main

    task = SimpleNamespace(done=lambda: False)
    runtime = SimpleNamespace(
        task=task,
        webhook_active=False,
        bot_info=SimpleNamespace(username="live_bot"),
    )
    monkeypatch.setattr(status_api.plugins, "get_plugin_config", lambda _name: {
        "bots": [
            {"name": "Live", "enabled": True, "token": "secret-token", "mode": "polling", "allowed_users": [1]},
            {"name": "Draft", "enabled": False, "token": "", "webhook_secret": "secret-hook"},
        ]
    })
    monkeypatch.setattr(bot_manager, "get_all_bots", lambda: {"Live": runtime})

    result = asyncio.run(status_api.Status(None, None).process({}, None))
    assert result["configured"] == 1
    assert result["running"] == 1
    assert result["bots"][0]["username"] == "@live_bot"
    assert "secret-token" not in json.dumps(result)
    assert "secret-hook" not in json.dumps(result)
