"""Tests for branding configuration module."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestBrandingDefaults:
    """Test default branding values when no env vars are set."""

    # Clear any BRAND_* env vars (e.g. from usr/.env loaded by python-dotenv)
    # so we test the hardcoded defaults in branding.py.
    _clear_env = {k: v for k, v in os.environ.items() if not k.startswith("BRAND_")}

    def test_default_brand_name(self):
        import importlib

        with patch.dict(os.environ, self._clear_env, clear=True):
            from python.helpers import branding

            importlib.reload(branding)
            assert branding.BRAND_NAME == "Apollos AI"

    def test_default_brand_slug(self):
        import importlib

        with patch.dict(os.environ, self._clear_env, clear=True):
            from python.helpers import branding

            importlib.reload(branding)
            assert branding.BRAND_SLUG == "apollos-ai"

    def test_default_brand_url(self):
        import importlib

        with patch.dict(os.environ, self._clear_env, clear=True):
            from python.helpers import branding

            importlib.reload(branding)
            assert branding.BRAND_URL == "https://matherly.net"

    def test_default_github_url(self):
        import importlib

        with patch.dict(os.environ, self._clear_env, clear=True):
            from python.helpers import branding

            importlib.reload(branding)
            assert (
                branding.BRAND_GITHUB_URL == "https://github.com/jrmatherly/apollos-ai"
            )


class TestBrandingEnvOverride:
    """Test that environment variables override defaults."""

    def test_custom_brand_name(self):
        import importlib

        with patch.dict(os.environ, {"BRAND_NAME": "Test AI"}):
            from python.helpers import branding

            importlib.reload(branding)
            assert branding.BRAND_NAME == "Test AI"

    def test_custom_brand_slug(self):
        import importlib

        with patch.dict(os.environ, {"BRAND_SLUG": "test-ai"}):
            from python.helpers import branding

            importlib.reload(branding)
            assert branding.BRAND_SLUG == "test-ai"

    def test_custom_brand_url(self):
        import importlib

        with patch.dict(os.environ, {"BRAND_URL": "https://test.ai"}):
            from python.helpers import branding

            importlib.reload(branding)
            assert branding.BRAND_URL == "https://test.ai"


class TestBrandingApi:
    """Test the branding API endpoint."""

    @pytest.mark.asyncio
    async def test_branding_get_returns_config(self):
        from python.api.branding_get import BrandingGet

        handler = BrandingGet(app=MagicMock(), thread_lock=MagicMock())
        result = await handler.process({}, None)
        assert "name" in result
        assert "slug" in result
        assert "url" in result
        assert "github_url" in result

    @pytest.mark.asyncio
    async def test_branding_get_no_auth_required(self):
        from python.api.branding_get import BrandingGet

        assert BrandingGet.requires_auth() is False
        assert BrandingGet.requires_csrf() is False
