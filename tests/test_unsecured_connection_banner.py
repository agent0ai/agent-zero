import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extensions.python.banners import _10_unsecured_connection as unsecured_connection


def test_unsecured_connection_banner_opens_authentication_settings(monkeypatch):
    monkeypatch.setattr(
        unsecured_connection.dotenv,
        "get_dotenv_value",
        lambda key, default="": "",
    )

    banners = []
    asyncio.run(
        unsecured_connection.UnsecuredConnectionCheck(agent=None).execute(
            banners=banners,
            frontend_context={"hostname": "agent.example.com", "protocol": "http:"},
        )
    )

    row = next(banner for banner in banners if banner.get("id") == "unsecured-connection")
    assert 'href="#section-auth"' in row["html"]
    assert 'data-banner-action="open-modal:settings/settings.html#section-auth"' in row["html"]
    assert "onclick" not in row["html"]
