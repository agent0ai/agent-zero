import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import files
from helpers.print_style import PrintStyle


class _PassthroughSecretsManager:
    def mask_values(self, text: str) -> str:
        return text


@pytest.fixture(autouse=True)
def _reset_print_style_state(tmp_path, monkeypatch):
    from helpers import secrets

    manager = secrets.SecretsManager(str(tmp_path / "usr/secrets.env"))
    monkeypatch.setattr(secrets, "get_secrets_manager", lambda: manager)
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(PrintStyle, "last_endline", True)
    monkeypatch.setattr(PrintStyle, "log_file_path", None)
    monkeypatch.setattr(PrintStyle, "_log_escape_tail", "")


def test_get_sanitizes_lone_surrogates():
    style = PrintStyle(log_only=True)
    style.secrets_mgr = _PassthroughSecretsManager()

    plain_text, styled_text, html_text = style.get("bad \ud83d")

    assert plain_text == "bad ?"
    assert "\ud83d" not in styled_text
    assert "\ud83d" not in html_text


def test_print_sanitizes_lone_surrogates_without_crash(capsys):
    style = PrintStyle()
    style.secrets_mgr = _PassthroughSecretsManager()

    style.print("bad \ud83d")

    content = capsys.readouterr().out

    assert "bad ?" in content
    assert "\ud83d" not in content


def _log_text():
    return Path(PrintStyle.log_file_path).read_text(encoding="utf-8")


def test_plain_file_preserves_whitespace_markup_and_masks_secrets(tmp_path, capsys):
    from helpers.secrets import SecretsManager

    (tmp_path / "usr").mkdir()
    (tmp_path / "usr/secrets.env").write_text('API_TOKEN="synthetic-secret"\n')
    style = PrintStyle(bold=True, italic=True, underline=True, font_color="red")
    style.secrets_mgr = SecretsManager("usr/secrets.env")
    payload = '<tag>&amp; & "quoted"\n\n  spaces\n\ttab Žluťoučký 🐈 synthetic-secret'

    style.print(payload)

    assert _log_text() == payload.replace("synthetic-secret", "§§secret(API_TOKEN)") + "\n"
    assert "\x1b[" in capsys.readouterr().out
    assert Path(PrintStyle.log_file_path).parent == tmp_path / "usr/logs"
    assert Path(PrintStyle.log_file_path).suffix == ".log"
    assert not (tmp_path / "logs").exists()


def test_stream_appends_chunks_and_print_keeps_existing_line_boundaries(capsys):
    style = PrintStyle(log_only=True)
    style.secrets_mgr = _PassthroughSecretsManager()
    for chunk in ['first ', '<b>literal</b>\n\n', '\t雪', '  end']:
        style.stream(chunk)
    assert _log_text() == "first <b>literal</b>\n\n\t雪  end"
    style.print("next", end="!")
    style.print("last")
    assert _log_text() == "first <b>literal</b>\n\n\t雪  end\nnext!\nlast\n"
    assert capsys.readouterr().out == ""


def test_file_removes_terminal_controls_including_split_sequences():
    style = PrintStyle(log_only=True)
    style.secrets_mgr = _PassthroughSecretsManager()
    for chunk in ['\x1b[3', '1mred\x1b[0m ', '\x1b]8;;https://example.test', '\x1b', '\\link', '\x1b]8;;\x07\n\t', 'tail\x07']:
        style.stream(chunk)
    assert _log_text() == "red link\n\ttail"


def test_unfinished_tool_escape_does_not_consume_later_records(capsys):
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import Mock
    from helpers.tool import Response, Tool

    agent = SimpleNamespace(agent_name="A0", hist_add_tool_result=Mock())
    tool = Tool(agent, "synthetic", None, {}, "", None)
    tool.log = SimpleNamespace(id="tool", update=Mock())
    payload = "before\x1b]0;unfinished title"

    asyncio.run(tool.after_execution(Response(payload, False)))
    PrintStyle.warning("still visible")
    PrintStyle.standard("ordinary")

    assert _log_text() == (
        "\nA0: Response from tool 'synthetic'\nbefore\n"
        "\nWarning: still visible\nordinary\n"
    )
    assert "Warning: still visible" in capsys.readouterr().out
    tool.log.update.assert_called_once_with(content=payload)


@pytest.mark.parametrize("escape", ["\x1b]0;unfinished title", "\x1b[31", "\x1b"])
@pytest.mark.parametrize("end", ["\n", "!", ""])
def test_incomplete_print_escape_preserves_end_and_next_stream(escape, end):
    style = PrintStyle(log_only=True)
    style.print("before" + escape, end=end)
    style.stream("after")
    assert _log_text() == "before" + end + "after"


def test_print_discards_unfinished_escape_from_previous_stream():
    style = PrintStyle(log_only=True)
    style.stream("before\x1b]0;unfinished title")
    style.print("next")
    style.stream("after")
    assert _log_text() == "before\nnext\nafter"


def test_record_ending_is_sanitized_before_masking(tmp_path):
    from helpers.secrets import SecretsManager

    (tmp_path / "usr").mkdir()
    (tmp_path / "usr/secrets.env").write_text('API_TOKEN="synthetic-secret"\n')
    style = PrintStyle(log_only=True)
    style.secrets_mgr = SecretsManager("usr/secrets.env")
    style.print("synthetic-", end="\x1b[31msecret\x1b[0m\n\x1b]0;unfinished")
    assert _log_text() == "§§secret(API_TOKEN)\n"


def test_warning_error_prefixes_and_padding():
    PrintStyle.warning("problem %s", "one")
    PrintStyle.error("problem %(name)s", {"name": "two"})
    assert _log_text() == "\nWarning: problem one\n\nError: problem two\n"


def test_new_log_never_overwrites_previous_run_and_ignores_cwd(tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    PrintStyle.standard("first run")
    first = Path(PrintStyle.log_file_path)
    PrintStyle.log_file_path = None
    PrintStyle.standard("second run")
    assert first != Path(PrintStyle.log_file_path)
    assert first.read_text() == "first run\n"
    assert _log_text() == "second run\n"
    assert not (elsewhere / "usr").exists()


def test_log_follows_user_data_directory_symlink(tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()
    (tmp_path / "usr").symlink_to(storage, target_is_directory=True)
    PrintStyle.standard("mounted data")
    assert Path(PrintStyle.log_file_path).resolve().parent == storage / "logs"
    assert _log_text() == "mounted data\n"


def test_file_failure_preserves_console_and_recovers(tmp_path, capsys):
    (tmp_path / "usr").write_text("not a directory")
    PrintStyle.standard("still visible")
    output = capsys.readouterr()
    assert "still visible" in output.out
    assert "Could not write application log" in output.err
    assert PrintStyle.log_file_path is None
    (tmp_path / "usr").unlink()
    PrintStyle.standard("recovered")
    assert _log_text() == "recovered\n"


def test_file_does_not_save_unmasked_payload_when_masking_fails():
    class BrokenSecrets:
        def mask_values(self, _text):
            raise RuntimeError("unavailable")

    style = PrintStyle(log_only=True)
    style.secrets_mgr = BrokenSecrets()
    style.print("synthetic-secret")
    assert "synthetic-secret" not in _log_text()
    assert "secret masking unavailable" in _log_text()


def test_existing_streaming_secret_filter_feeds_plain_file():
    from helpers.secrets import StreamingSecretsFilter

    secret_filter = StreamingSecretsFilter({"TOKEN": "synthetic-secret"})
    for chunk in ["  token: synt", "hetic-", "secret\n\tUnicode 雪"]:
        PrintStyle(log_only=True).stream(secret_filter.process_chunk(chunk))
    PrintStyle(log_only=True).stream(secret_filter.finalize())
    assert _log_text() == "  token: §§secret(TOKEN)\n\tUnicode 雪"


def test_concurrent_records_are_appended_whole():
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda n: PrintStyle(log_only=True).print(f"record-{n}"), range(20)))
    assert sorted(_log_text().splitlines()) == sorted(f"record-{n}" for n in range(20))
