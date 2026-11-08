import os
import sys
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


def activate():
    source = ROOT / "requirements.py"
    exec(compile(source.read_text(), str(source), "exec"), {"__file__": str(source)})


class Conflict(Exception):
    def __init__(self, manifest, candidates):
        self.manifest = manifest
        self.candidates = candidates


@pytest.fixture
def bootstrap(monkeypatch, tmp_path):
    manifest = tmp_path / "imports.lock"
    error = Conflict(manifest, ["packaging: already imported from global site-packages"])

    def activate(path):
        assert path == ROOT / "requirements.txt"
        raise error

    monkeypatch.setitem(sys.modules, "depfix", SimpleNamespace(
        default_requirements=activate, SharedImportConflictError=Conflict,
    ))
    monkeypatch.setattr(sys, "argv", [str(ROOT / "run_ui.py"), "--dockerized=true"])
    monkeypatch.setattr(sys, "orig_argv", [sys.executable, "-m", "depfix", "run", *sys.argv])
    monkeypatch.delenv("A0_DEPFIX_BOOTSTRAP", raising=False)
    return error


@pytest.mark.parametrize("previous", ["/existing/imports", ""])
def test_bootstrap_restarts_with_selected_loader_graph(monkeypatch, tmp_path, bootstrap, previous):
    nodes = [
        SimpleNamespace(id="loader", distribution="depfix", artifact="loader", dependencies={"packaging": "packaging"}),
        SimpleNamespace(id="packaging", distribution="packaging", artifact="packaging", dependencies={}),
    ]
    for node in nodes:
        (tmp_path / node.artifact / "purelib").mkdir(parents=True)
    graph = SimpleNamespace(nodes=nodes, node_index={node.id: node for node in nodes})
    monkeypatch.setitem(sys.modules, "depfix.manifest", SimpleNamespace(load_manifest=lambda path: graph))
    monkeypatch.setitem(sys.modules, "depfix.cache", SimpleNamespace(
        Cache=lambda root: SimpleNamespace(unpacked_path=lambda artifact: root / artifact),
    ))
    monkeypatch.setitem(sys.modules, "depfix.settings", SimpleNamespace(
        resolve_settings=lambda: SimpleNamespace(cache_dir=tmp_path),
    ))
    monkeypatch.setenv("PYTHONPATH", previous)
    calls = []
    monkeypatch.setattr(os, "execve", lambda *args: calls.append(args))

    activate()

    executable, argv, env = calls[0]
    assert executable == sys.executable
    assert argv == sys.orig_argv
    assert env["A0_DEPFIX_BOOTSTRAP"] == str(bootstrap.manifest)
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert env["PYTHONPATH"].split(os.pathsep) == [
        str(tmp_path / "loader" / "purelib"),
        str(tmp_path / "packaging" / "purelib"),
    ] + ([previous] if previous else [])


@pytest.mark.parametrize("reason", ["repeated", "application_owner", "embedded"])
def test_bootstrap_preserves_other_conflicts(monkeypatch, bootstrap, reason):
    if reason == "repeated":
        monkeypatch.setenv("A0_DEPFIX_BOOTSTRAP", str(bootstrap.manifest))
    elif reason == "application_owner":
        bootstrap.candidates = ["numpy: already imported from another graph"]
    else:
        monkeypatch.setattr(sys, "argv", ["-c"])
    monkeypatch.setattr(os, "execve", lambda *args: pytest.fail("Unexpected restart"))

    with pytest.raises(Conflict) as caught:
        activate()
    assert caught.value is bootstrap


@pytest.mark.skipif(sys.platform != "linux", reason="Linux startup serialization")
def test_activation_holds_process_lock_until_finished(tmp_path):
    import fcntl

    source = tmp_path / "requirements.py"
    source.write_text((ROOT / "requirements.py").read_text())
    script = """
import runpy, sys
from types import SimpleNamespace
def activate(path):
    print('activating', flush=True)
    assert sys.stdin.readline().strip() == 'finish'
sys.modules['depfix'] = SimpleNamespace(default_requirements=activate)
runpy.run_path(sys.argv[1])
"""
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(source)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    try:
        assert process.stdout.readline().strip() == "activating"
        with (tmp_path / "tmp/requirements.lock").open("a") as lock:
            with pytest.raises(BlockingIOError):
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            process.communicate("finish\n", timeout=10)
            assert process.returncode == 0
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
