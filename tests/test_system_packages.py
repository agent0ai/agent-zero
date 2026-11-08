import os
from pathlib import Path
import subprocess

import pytest

from helpers import system_packages


@pytest.mark.parametrize("os_id", ["kali", "debian", "ubuntu"])
def test_runtime_apt_preserves_command_and_source_settings(tmp_path, monkeypatch, os_id):
    sources = (tmp_path / "sources.list", tmp_path / "kali.sources")
    contents = (
        "# Local mirror\ndeb https://mirror.example/kali kali-rolling main contrib\n",
        "Types: deb\nURIs: https://mirror.example/kali\nSuites: kali-rolling\nComponents: main\nSigned-By: /keyring.gpg\n",
    )
    for source, content in zip(sources, contents):
        source.write_text(content)
    monkeypatch.setattr(system_packages, "KALI_SOURCE_FILES", sources)
    monkeypatch.setattr(system_packages.platform, "freedesktop_os_release", lambda: {"ID": os_id})
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(system_packages.subprocess, "run", run)
    command = ["apt-get", "install", "-y", "python3-uno"]
    for _ in range(2):
        assert system_packages.run_runtime_apt(command, timeout=30).returncode == 0
        for source, content in zip(sources, contents):
            expected = content.replace("kali-rolling", "kali-last-snapshot") if os_id == "kali" else content
            assert source.read_text() == expected
        assert commands[-1] == command
    assert command == ["apt-get", "install", "-y", "python3-uno"]


def test_runtime_apt_propagates_source_write_errors(tmp_path, monkeypatch):
    source = tmp_path / "sources.list"
    source.write_text("deb https://mirror.example/kali kali-rolling main\n")
    monkeypatch.setattr(system_packages, "KALI_SOURCE_FILES", (source,))
    monkeypatch.setattr(system_packages.platform, "freedesktop_os_release", lambda: {"ID": "kali"})

    def fail_write(*args, **kwargs):
        raise PermissionError("source is read-only")

    monkeypatch.setattr(Path, "write_text", fail_write)
    monkeypatch.setattr(system_packages.subprocess, "run", lambda *args, **kwargs: pytest.fail("APT must not run"))
    with pytest.raises(PermissionError, match="source is read-only"):
        system_packages.run_runtime_apt(["apt-get", "install", "python3-gi-cairo"], timeout=30)
