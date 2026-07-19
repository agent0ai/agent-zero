from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from helpers import files, state_migration, system_packages


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_NAME = "_office"
STATE_DIR = Path(files.get_abs_path("usr", "plugins", PLUGIN_NAME))
RETIRED_STATE_DIR = Path(files.get_abs_path("usr", PLUGIN_NAME))
DOCUMENT_STATE_DIR = STATE_DIR / "documents"
LEGACY_DOCUMENT_STATE_DIRS = [
    RETIRED_STATE_DIR / "documents",
    Path(files.get_abs_path("usr", "state", "_office", "documents")),
    Path(files.get_abs_path("usr", "state", "office", "documents")),
]
RETIRED_WEB_APT_SOURCE_FILE = Path("/etc/apt/sources.list.d/collaboraonline.sources")
RETIRED_WEB_APT_KEYRING_FILE = Path("/etc/apt/keyrings/collaboraonline-release-keyring.gpg")
RETIRED_WEB_SUPERVISOR_FILE = Path("/etc/supervisor/conf.d/a0_office_collabora.conf")
RETIRED_WEB_SUPERVISOR_PROGRAM = "a0_office_collabora"
RETIRED_WEB_RUNTIME_DIRS = [
    Path("/opt/cool"),
    Path("/opt/collaboraoffice"),
    Path("/a0/tmp/_office/collabora"),
    Path("/a0/usr/plugins/_office/collabora"),
    PROJECT_ROOT / "tmp" / "_office" / "collabora",
    PROJECT_ROOT / "usr" / "plugins" / "_office" / "collabora",
]
RETIRED_WEB_PACKAGES = (
    "coolwsd",
    "coolwsd-deprecated",
    "code-brand",
    "collaboraoffice",
    "collaboraoffice-ure",
    "collaboraofficebasis-calc",
    "collaboraofficebasis-core",
    "collaboraofficebasis-draw",
    "collaboraofficebasis-en-us",
    "collaboraofficebasis-extension-pdf-import",
    "collaboraofficebasis-graphicfilter",
    "collaboraofficebasis-images",
    "collaboraofficebasis-impress",
    "collaboraofficebasis-math",
    "collaboraofficebasis-ooolinguistic",
    "collaboraofficebasis-ooofonts",
    "collaboraofficebasis-writer",
)
RUNTIME_PACKAGES = (
    "libreoffice-core",
    "libreoffice-writer",
    "libreoffice-calc",
    "libreoffice-impress",
    "libreoffice-gtk3",
    "python3-uno",
    "fonts-dejavu",
    "fonts-liberation",
    "fonts-crosextra-caladea",
    "fonts-crosextra-carlito",
    "fonts-noto-core",
    "fonts-noto-cjk",
    "fonts-noto-color-emoji",
)
RETIRED_RUNTIME_PACKAGES = (
    "firefox-esr",
)
CLEANUP_MARKER = STATE_DIR / "stale-cleanup-v3.done"


def cleanup_stale_runtime_state(force: bool = False) -> dict[str, Any]:
    """Prepare the LibreOffice runtime and remove retired office state.

    The hook is intentionally idempotent: existing dependencies, missing stale
    files, packages, and processes count as already clean. It is safe to call
    during startup and self-update.
    """

    removed: list[str] = []
    installed: list[str] = []
    migrated: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    _migrate_retired_plugin_state(migrated, warnings, errors)
    _migrate_legacy_document_state(migrated, warnings, errors)

    retired_web_paths = [
        path
        for path in [
            RETIRED_WEB_APT_SOURCE_FILE,
            RETIRED_WEB_APT_KEYRING_FILE,
            RETIRED_WEB_SUPERVISOR_FILE,
            *RETIRED_WEB_RUNTIME_DIRS,
        ]
        if path.exists() or path.is_symlink()
    ]
    retired_web_packages = _installed_retired_web_packages()
    cleanup_needed = force or not CLEANUP_MARKER.exists() or bool(retired_web_paths or retired_web_packages)

    if cleanup_needed:
        _cleanup_retired_web_runtime(
            removed,
            errors,
            retired_web_packages=retired_web_packages,
            purge_packages=True,
        )

        try:
            CLEANUP_MARKER.parent.mkdir(parents=True, exist_ok=True)
            CLEANUP_MARKER.write_text("ok\n", encoding="utf-8")
        except Exception as exc:
            errors.append(f"{CLEANUP_MARKER}: {exc}")

    retired_packages = [
        package
        for package in _installed_packages(RETIRED_RUNTIME_PACKAGES)
        if package not in retired_web_packages
    ]
    if retired_packages:
        _purge_packages(removed, errors, installed_packages=retired_packages)

    _retire_supervisor_program(errors)
    _ensure_runtime_dependencies(installed, errors)
    _ensure_desktop_runtime_compat(installed, removed, migrated, warnings, errors)
    return {
        "ok": not errors,
        "skipped": not cleanup_needed,
        "removed": removed,
        "installed": installed,
        "migrated": migrated,
        "warnings": warnings,
        "errors": errors,
    }


def retire_collabora_web_runtime(force: bool = False) -> dict[str, Any]:
    """Retire the legacy Collabora web runtime without preparing LibreOffice.

    This is intentionally narrower than cleanup_stale_runtime_state(). Older
    Docker self-update managers run the checked-out repo's prepare.py before the
    updated UI starts, so prepare.py can call this fast hook to remove the stale
    supervisor program left by v1.10 without blocking health checks on desktop
    package installation.
    """

    removed: list[str] = []
    errors: list[str] = []
    retired_web_paths = [
        path
        for path in [
            RETIRED_WEB_APT_SOURCE_FILE,
            RETIRED_WEB_APT_KEYRING_FILE,
            RETIRED_WEB_SUPERVISOR_FILE,
            *RETIRED_WEB_RUNTIME_DIRS,
        ]
        if path.exists() or path.is_symlink()
    ]

    if force or retired_web_paths:
        _cleanup_retired_web_runtime(
            removed,
            errors,
            retired_web_packages=[],
            purge_packages=False,
        )

    return {
        "ok": not errors,
        "skipped": not force and not retired_web_paths,
        "removed": removed,
        "errors": errors,
    }


def _migrate_legacy_document_state(
    migrated: list[str],
    warnings: list[str],
    errors: list[str],
) -> None:
    legacy_dirs = [
        path
        for path in LEGACY_DOCUMENT_STATE_DIRS
        if path != DOCUMENT_STATE_DIR and path.exists()
    ]
    if not legacy_dirs:
        return

    if DOCUMENT_STATE_DIR.exists():
        warnings.extend(
            f"Legacy Office document state left in place because {DOCUMENT_STATE_DIR} already exists: {path}"
            for path in legacy_dirs
        )
        return

    source = legacy_dirs[0]
    try:
        DOCUMENT_STATE_DIR.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, DOCUMENT_STATE_DIR, symlinks=True)
        migrated.append(f"{source} -> {DOCUMENT_STATE_DIR}")
    except Exception as exc:
        errors.append(f"Office document state migration failed from {source}: {exc}")
        return

    warnings.extend(
        f"Additional legacy Office document state left in place after migrating {source}: {path}"
        for path in legacy_dirs[1:]
    )


def _migrate_retired_plugin_state(
    migrated: list[str],
    warnings: list[str],
    errors: list[str],
) -> None:
    state_migration.migrate_retired_state_tree(
        source=RETIRED_STATE_DIR,
        destination=STATE_DIR,
        owner="Office",
        migrated=migrated,
        warnings=warnings,
        errors=errors,
    )


def _ensure_desktop_runtime_compat(
    installed: list[str],
    removed: list[str],
    migrated: list[str],
    warnings: list[str],
    errors: list[str],
) -> None:
    """Keep self-update compatibility for managers that only invoke _office/hooks.py.

    Agent Zero 1.10-1.13 self-update managers call the Office cleanup hook
    directly before starting the updated UI. Desktop runtime ownership now lives
    in _desktop, so this temporary delegate preserves the old pre-launch cleanup
    and package-preparation behavior for users updating from those releases.
    """

    try:
        from plugins._desktop import hooks as desktop_hooks
    except Exception as exc:
        warnings.append(f"Desktop runtime compatibility hook unavailable: {exc}")
        return

    try:
        result = desktop_hooks.cleanup_stale_runtime_state()
    except Exception as exc:
        errors.append(f"Desktop runtime compatibility hook failed: {exc}")
        return

    if not isinstance(result, dict):
        return
    installed.extend(str(item) for item in result.get("installed") or [])
    removed.extend(str(item) for item in result.get("removed") or [])
    migrated.extend(str(item) for item in result.get("migrated") or [])
    warnings.extend(str(item) for item in result.get("warnings") or [])
    errors.extend(str(item) for item in result.get("errors") or [])


def _remove_path(path: Path) -> bool:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return True
    if path.exists():
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass
        return True
    return False


def _cleanup_retired_web_runtime(
    removed: list[str],
    errors: list[str],
    *,
    retired_web_packages: list[str],
    purge_packages: bool,
) -> None:
    _stop_supervisor_program(errors)
    _kill_old_processes(errors)

    for path in [
        RETIRED_WEB_APT_SOURCE_FILE,
        RETIRED_WEB_APT_KEYRING_FILE,
        RETIRED_WEB_SUPERVISOR_FILE,
        *RETIRED_WEB_RUNTIME_DIRS,
    ]:
        try:
            if _remove_path(path):
                removed.append(str(path))
        except Exception as exc:
            errors.append(f"{path}: {exc}")

    _retire_supervisor_program(errors)
    if purge_packages:
        _purge_packages(removed, errors, installed_packages=retired_web_packages)


def _kill_old_processes(errors: list[str]) -> None:
    if not shutil.which("pkill"):
        return
    result = subprocess.run(
        ["pkill", "-f", "coolwsd"],
        check=False,
        text=True,
        capture_output=True,
        timeout=8,
    )
    if result.returncode not in {0, 1}:
        errors.append((result.stderr or result.stdout or "pkill coolwsd failed").strip())


def _stop_supervisor_program(errors: list[str]) -> None:
    if not shutil.which("supervisorctl"):
        return
    status = _supervisorctl("status", RETIRED_WEB_SUPERVISOR_PROGRAM)
    status_output = _supervisor_output(status)
    if status.returncode != 0:
        if _supervisor_absent(status_output) or _supervisor_stopped(status_output):
            return
        errors.append(status_output or f"supervisorctl status {RETIRED_WEB_SUPERVISOR_PROGRAM} failed")
        return

    if _supervisor_stopped(status_output):
        return

    stopped = _supervisorctl("stop", RETIRED_WEB_SUPERVISOR_PROGRAM)
    stopped_output = _supervisor_output(stopped)
    if stopped.returncode != 0 and not (
        _supervisor_absent(stopped_output) or _supervisor_stopped(stopped_output)
    ):
        errors.append(stopped_output or f"supervisorctl stop {RETIRED_WEB_SUPERVISOR_PROGRAM} failed")


def _retire_supervisor_program(errors: list[str]) -> None:
    if not shutil.which("supervisorctl"):
        return
    status = _supervisorctl("status", RETIRED_WEB_SUPERVISOR_PROGRAM)
    status_output = _supervisor_output(status)
    if status.returncode != 0:
        if _supervisor_absent(status_output):
            return
        if not _supervisor_stopped(status_output):
            errors.append(status_output or f"supervisorctl status {RETIRED_WEB_SUPERVISOR_PROGRAM} failed")
            return

    if not _supervisor_stopped(status_output):
        stopped = _supervisorctl("stop", RETIRED_WEB_SUPERVISOR_PROGRAM)
        stopped_output = _supervisor_output(stopped)
        if stopped.returncode != 0 and not (
            _supervisor_absent(stopped_output) or _supervisor_stopped(stopped_output)
        ):
            errors.append(stopped_output or f"supervisorctl stop {RETIRED_WEB_SUPERVISOR_PROGRAM} failed")
            return

    removed = _supervisorctl("remove", RETIRED_WEB_SUPERVISOR_PROGRAM)
    removed_output = _supervisor_output(removed)
    if removed.returncode != 0 and not _supervisor_absent(removed_output):
        errors.append(removed_output or f"supervisorctl remove {RETIRED_WEB_SUPERVISOR_PROGRAM} failed")
        return

    for command in (("reread",), ("update",)):
        result = _supervisorctl(*command)
        output = _supervisor_output(result)
        if result.returncode != 0 and not _supervisor_absent(output):
            errors.append(output or f"supervisorctl {' '.join(command)} failed")


def _supervisorctl(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["supervisorctl", *args],
        check=False,
        text=True,
        capture_output=True,
        timeout=15,
    )


def _supervisor_output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout or "").strip()


def _supervisor_absent(output: str) -> bool:
    normalized = output.lower()
    return (
        "no such process" in normalized
        or "no such group" in normalized
        or "not running" in normalized
        or "unix:///var/run/supervisor.sock" in normalized
        or "connection refused" in normalized
        or "no such file" in normalized
    )


def _supervisor_stopped(output: str) -> bool:
    return bool(re.search(rf"(^|\s){re.escape(RETIRED_WEB_SUPERVISOR_PROGRAM)}\s+STOPPED\b", output))


def _installed_packages(packages: tuple[str, ...]) -> list[str]:
    if not shutil.which("dpkg-query"):
        return []
    return [package for package in packages if _package_installed(package)]


def _installed_retired_web_packages() -> list[str]:
    packages = [
        *_installed_packages(RETIRED_WEB_PACKAGES),
        *_installed_collabora_packages(),
    ]
    return list(dict.fromkeys(packages))


def _installed_collabora_packages() -> list[str]:
    if not shutil.which("dpkg-query"):
        return []

    result = subprocess.run(
        ["dpkg-query", "-W", "-f=${binary:Package}\t${Status}\n", "collaboraoffice*"],
        check=False,
        text=True,
        capture_output=True,
        timeout=15,
    )

    packages: list[str] = []
    for line in result.stdout.splitlines():
        package, _, status = line.partition("\t")
        if package.startswith("collaboraoffice") and "install ok installed" in status:
            packages.append(package)
    return packages


def _purge_packages(
    removed: list[str],
    errors: list[str],
    *,
    installed_packages: list[str] | None = None,
) -> None:
    if os.geteuid() != 0 or not shutil.which("apt-get") or not shutil.which("dpkg-query"):
        return
    installed = installed_packages if installed_packages is not None else _installed_retired_web_packages()
    if not installed:
        return
    result = _run_apt_command(["apt-get", "purge", "-y", *installed], timeout=180)
    if result.returncode == 0:
        removed.extend(installed)
        return
    errors.append((result.stderr or result.stdout or "apt-get purge failed").strip())


def _package_installed(package: str) -> bool:
    result = subprocess.run(
        ["dpkg-query", "-W", "-f=${Status}", package],
        check=False,
        text=True,
        capture_output=True,
        timeout=8,
    )
    return result.returncode == 0 and "install ok installed" in result.stdout


def _ensure_runtime_dependencies(installed: list[str], errors: list[str]) -> None:
    if os.geteuid() != 0 or not shutil.which("apt-get") or not shutil.which("dpkg-query"):
        return
    missing = [package for package in RUNTIME_PACKAGES if not _package_installed(package)]
    if not missing:
        return

    if not _apt_update(errors):
        return

    _install_runtime_packages(missing, installed, errors)


def _install_runtime_packages(
    packages: list[str],
    installed: list[str],
    errors: list[str],
) -> bool:
    result = _run_apt_command(["apt-get", "install", "-y", "--no-install-recommends", *packages], timeout=900)
    if result.returncode == 0:
        installed.extend(packages)
        return True
    output = (result.stderr or result.stdout or "apt-get install failed").strip()
    errors.append(output)
    return False


def _apt_update(errors: list[str]) -> bool:
    result = _run_apt_command(["apt-get", "update"], timeout=300)
    if result.returncode == 0:
        return True
    errors.append((result.stderr or result.stdout or "apt-get update failed").strip())
    return False


def _run_apt_command(command: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    return system_packages.run_apt_with_retries(
        lambda: subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
            env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"},
        )
    )
