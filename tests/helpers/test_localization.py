"""Tests for python/helpers/localization.py."""

from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Reset singleton between tests
@pytest.fixture(autouse=True)
def reset_localization_singleton():
    from python.helpers import localization

    old = localization.Localization._instance
    localization.Localization._instance = None
    yield
    localization.Localization._instance = old


class TestLocalizationGet:
    def test_returns_singleton(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            a = Localization.get()
            b = Localization.get()
            assert a is b


class TestLocalizationInit:
    def test_default_timezone_utc(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                loc = Localization.get()
                assert loc.get_timezone() == "UTC"
                assert loc.get_offset_minutes() == 0

    def test_explicit_timezone_override(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value", return_value="UTC"):
            with patch("python.helpers.localization.save_dotenv_value"):
                with patch("python.helpers.localization.PrintStyle"):
                    loc = Localization(timezone="America/New_York")
                    assert loc.get_timezone() == "America/New_York"


class TestLocalizationComputeOffset:
    def test_utc_offset_zero(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                loc = Localization.get()
                assert loc._compute_offset_minutes("UTC") == 0


class TestLocalizationSetTimezone:
    def test_valid_timezone_updates(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                with patch("python.helpers.localization.PrintStyle"):
                    loc = Localization.get()
                    loc.set_timezone("Europe/London")
                    assert loc.get_timezone() == "Europe/London"

    def test_invalid_timezone_defaults_to_utc(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                with patch("python.helpers.localization.PrintStyle"):
                    loc = Localization.get()
                    loc.set_timezone("Invalid/Timezone")
                    assert loc.get_timezone() == "UTC"
                    assert loc.get_offset_minutes() == 0


class TestLocaltimeStrToUtcDt:
    def test_none_returns_none(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                loc = Localization.get()
                assert loc.localtime_str_to_utc_dt(None) is None

    def test_empty_string_returns_none(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                loc = Localization.get()
                assert loc.localtime_str_to_utc_dt("") is None

    def test_valid_iso_string_returns_utc_dt(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                with patch("python.helpers.localization.PrintStyle"):
                    loc = Localization.get()
                    result = loc.localtime_str_to_utc_dt("2024-01-15T12:00:00")
                    assert result is not None
                    assert result.tzinfo == timezone.utc


class TestUtcDtToLocaltimeStr:
    def test_none_returns_none(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                loc = Localization.get()
                assert loc.utc_dt_to_localtime_str(None) is None

    def test_utc_dt_converts_to_iso_string(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                loc = Localization.get()
                utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
                result = loc.utc_dt_to_localtime_str(utc_dt)
                assert result is not None
                assert "2024-01-15" in result
                assert "12:00" in result


class TestSerializeDatetime:
    def test_none_returns_none(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                loc = Localization.get()
                assert loc.serialize_datetime(None) is None

    def test_datetime_returns_iso_string(self):
        from python.helpers.localization import Localization

        with patch("python.helpers.localization.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "UTC" if k == "DEFAULT_USER_TIMEZONE" else ("0" if k == "DEFAULT_USER_UTC_OFFSET_MINUTES" else d)
            with patch("python.helpers.localization.save_dotenv_value"):
                loc = Localization.get()
                dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
                result = loc.serialize_datetime(dt)
                assert result is not None
                assert "2024-01-15" in result
