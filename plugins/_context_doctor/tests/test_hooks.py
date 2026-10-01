import sys

from plugins._context_doctor import hooks
from plugins._context_doctor.extensions.python.startup_migration import (
    _20_context_doctor_runtime as startup_runtime,
)


def test_dependency_check_requires_root_pinned_version(monkeypatch):
    requirement = hooks._json_repair_requirement()
    expected_version = requirement.partition("==")[2]

    monkeypatch.setattr(hooks.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(
        hooks.importlib.metadata, "version", lambda _name: expected_version
    )
    assert hooks._json_repair_is_current(requirement)

    monkeypatch.setattr(
        hooks.importlib.metadata, "version", lambda _name: f"{expected_version}.stale"
    )
    assert not hooks._json_repair_is_current(requirement)


def test_dependency_hook_installs_root_pinned_requirement(monkeypatch):
    requirement = hooks._json_repair_requirement()
    checks = iter((False, True))
    calls = []

    monkeypatch.setattr(
        hooks, "_json_repair_is_current", lambda _candidate: next(checks)
    )
    monkeypatch.setattr(hooks.shutil, "which", lambda _command: "/usr/local/bin/uv")
    monkeypatch.setattr(
        hooks.subprocess,
        "check_call",
        lambda command, cwd: calls.append((command, cwd)),
    )

    assert requirement.startswith("json_repair==")
    assert hooks.ensure_dependencies()
    assert calls == [
        (
            [
                "/usr/local/bin/uv",
                "pip",
                "install",
                "--python",
                sys.executable,
                requirement,
            ],
            str(hooks._PLUGIN_DIR),
        )
    ]


def test_startup_migration_calls_dependency_hook(monkeypatch):
    calls = []
    monkeypatch.setattr(
        startup_runtime,
        "call_plugin_hook",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    startup_runtime.ContextDoctorRuntime(None).execute()

    assert calls == [
        (("_context_doctor", "ensure_dependencies"), {"raise_on_error": False})
    ]
