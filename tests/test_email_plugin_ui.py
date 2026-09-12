import asyncio
from pathlib import Path

import yaml

from plugins._email_integration.api.status import Status


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "_email_integration"


def test_email_plugin_exposes_scoped_config_and_shared_webui():
    metadata = yaml.safe_load((PLUGIN / "plugin.yaml").read_text())
    config_html = (PLUGIN / "webui" / "config.html").read_text()
    main_html = (PLUGIN / "webui" / "main.html").read_text()

    assert metadata["per_project_config"] is True
    assert metadata["per_agent_config"] is True
    assert "settings-advanced-section" in config_html
    assert 'class="email-advanced"' not in config_html
    assert "var(--color-" in main_html


def test_email_status_omits_credentials(monkeypatch):
    config = {
        "handlers": [{
            "name": "Support",
            "enabled": True,
            "account_type": "imap",
            "username": "support@example.com",
            "password": "super-secret",
            "imap_server": "imap.example.com",
            "smtp_server": "smtp.example.com",
        }]
    }
    monkeypatch.setattr(
        "plugins._email_integration.api.status.plugins.get_plugin_config",
        lambda name: config,
    )

    result = asyncio.run(Status().process({}, None))

    assert result["inboxes"][0]["configured"] is True
    assert "super-secret" not in repr(result)
