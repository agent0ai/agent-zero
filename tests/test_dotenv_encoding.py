import os

import pytest

from helpers import dotenv, files


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    (tmp_path / "usr").mkdir()
    return tmp_path / "usr" / ".env"


def test_save_dotenv_value_writes_utf8_bytes(env_file):
    dotenv.save_dotenv_value("TEST_PASSWORD", "café")
    data = env_file.read_bytes()
    assert "café".encode("utf-8") in data


def test_save_dotenv_value_round_trips_non_ascii_value(env_file):
    try:
        dotenv.save_dotenv_value("TEST_PASSWORD", "café-ünïcode")
        dotenv.load_dotenv()
        assert os.environ["TEST_PASSWORD"] == "café-ünïcode"
    finally:
        os.environ.pop("TEST_PASSWORD", None)


def test_save_dotenv_value_heals_legacy_locale_encoded_file(env_file):
    # A .env written by a locale-encoded save on a classic Windows process
    # contains non-UTF-8 bytes; saving again must not crash and must leave
    # a valid UTF-8 file with the untouched keys preserved.
    env_file.write_bytes("TEST_PASSWORD=caf\xe9\nOTHER_KEY=1\n".encode("cp1252"))
    dotenv.save_dotenv_value("TEST_PASSWORD", "café")
    data = env_file.read_bytes()
    assert "café".encode("utf-8") in data
    assert "OTHER_KEY=1" in data.decode("utf-8")
