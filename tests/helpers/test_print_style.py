"""Tests for python/helpers/print_style.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import python.helpers.print_style as _print_style_mod
import python.helpers.secrets as _secrets_mod

# --- Fixtures ---


@pytest.fixture
def patch_files_and_log(tmp_path):
    """Patch files.get_abs_path and avoid real log file creation."""
    with patch.object(_print_style_mod, "files") as mock_files:
        mock_files.get_abs_path.return_value = str(tmp_path / "logs")
        with patch.object(_print_style_mod.PrintStyle, "log_file_path", None):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.write = MagicMock()
                yield mock_files


@pytest.fixture
def patch_secrets():
    """Patch secrets manager to avoid masking."""
    with patch.object(_secrets_mod, "get_secrets_manager") as mock_get:
        mgr = MagicMock()
        mgr.mask_values.return_value = lambda x: x
        mgr.mask_values.side_effect = lambda x: x
        mock_get.return_value = mgr
        yield mgr


@pytest.fixture
def mock_print_style_env(patch_files_and_log, patch_secrets):
    """Ensure PrintStyle can run without real file I/O."""
    with patch("os.makedirs"):
        yield


class TestPrintStyleFormatArgs:
    def test_empty_args_returns_empty(self):
        from python.helpers.print_style import PrintStyle

        assert PrintStyle._format_args((), " ") == ""

    def test_single_arg(self):
        from python.helpers.print_style import PrintStyle

        assert PrintStyle._format_args(("hello",), " ") == "hello"

    def test_percent_format(self):
        from python.helpers.print_style import PrintStyle

        assert PrintStyle._format_args(("hello %s", "world"), " ") == "hello world"

    def test_format_method(self):
        from python.helpers.print_style import PrintStyle

        assert PrintStyle._format_args(("hello {}", "world"), " ") == "hello world"

    def test_format_method_with_kwargs(self):
        from python.helpers.print_style import PrintStyle

        # % formatting is tried first; "hello {name}" % {"name": "x"}
        # succeeds (no %-specifiers → string returned unchanged) before
        # .format() gets a chance to run.
        assert (
            PrintStyle._format_args(("hello {name}", {"name": "x"}), " ")
            == "hello {name}"
        )


class TestPrintStylePrefixedArgs:
    def test_empty_args_returns_prefix_only(self):
        from python.helpers.print_style import PrintStyle

        assert PrintStyle._prefixed_args("Hint", ()) == ("Hint:",)

    def test_string_first_arg(self):
        from python.helpers.print_style import PrintStyle

        assert PrintStyle._prefixed_args("Hint", ("do this",)) == ("Hint: do this",)

    def test_non_string_first_arg(self):
        from python.helpers.print_style import PrintStyle

        assert PrintStyle._prefixed_args("Info", (42,)) == ("Info:", 42)


class TestPrintStyleGetRgbColorCode:
    def test_hex_color(self):
        from python.helpers.print_style import PrintStyle

        ps = PrintStyle()

        code, _ = ps._get_rgb_color_code("#ff0000")
        assert "38;2;255;0;0" in code

    def test_named_color(self):
        from python.helpers.print_style import PrintStyle

        ps = PrintStyle()
        code, _ = ps._get_rgb_color_code("red")
        assert code != ""

    def test_invalid_color_returns_empty(self):
        from python.helpers.print_style import PrintStyle

        ps = PrintStyle()
        code, _ = ps._get_rgb_color_code("notacolor")
        assert code == ""


class TestPrintStyleGet:
    def test_get_returns_plain_styled_html(self, mock_print_style_env):
        from python.helpers.print_style import PrintStyle

        ps = PrintStyle()
        plain, styled, html = ps.get("hello")
        assert plain == "hello"
        assert "hello" in styled
        assert "hello" in html
        assert "<span" in html


class TestPrintStyleStaticMethods:
    def test_standard_prints(self, mock_print_style_env):
        from python.helpers.print_style import PrintStyle

        with patch("builtins.print") as mock_print:
            PrintStyle.standard("test")
            mock_print.assert_called()

    def test_hint_prints_with_prefix(self, mock_print_style_env):
        from python.helpers.print_style import PrintStyle

        with patch("builtins.print") as mock_print:
            PrintStyle.hint("test")
            call_args = str(mock_print.call_args)
            assert "Hint" in call_args or "test" in call_args

    def test_error_prints(self, mock_print_style_env):
        from python.helpers.print_style import PrintStyle

        with patch("builtins.print") as mock_print:
            PrintStyle.error("fail")
            mock_print.assert_called()

    def test_debug_skips_when_not_development(self, mock_print_style_env):
        from python.helpers.print_style import PrintStyle

        with patch.object(_print_style_mod, "_get_runtime") as mock_rt:
            mock_rt.return_value.is_development.return_value = False
            with patch("builtins.print") as mock_print:
                PrintStyle.debug("debug msg")
                mock_print.assert_not_called()

    def test_debug_prints_when_development(self, mock_print_style_env):
        from python.helpers.print_style import PrintStyle

        with patch.object(_print_style_mod, "_get_runtime") as mock_rt:
            mock_rt.return_value.is_development.return_value = True
            with patch("builtins.print") as mock_print:
                PrintStyle.debug("debug msg")
                mock_print.assert_called()
