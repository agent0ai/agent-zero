"""Just-in-time system dependencies for legacy OCR fallbacks."""

from __future__ import annotations

import os
import shutil
import subprocess
import threading

import logging
import time


TESSERACT_APT_PACKAGES = (
    "tesseract-ocr",
    "tesseract-ocr-script-latn",
)
POPPLER_APT_PACKAGES = ("poppler-utils",)

_INSTALL_LOCK = threading.RLock()
_READY_PROFILES: set[str] = set()


def ensure_tesseract_dependencies() -> None:
    """Ensure the system Tesseract executable and Latin language data exist."""
    _ensure_dependencies(
        profile="tesseract",
        packages=TESSERACT_APT_PACKAGES,
        commands=("tesseract",),
    )


def ensure_pdf_ocr_dependencies() -> None:
    """Ensure Tesseract plus the Poppler commands used by pdf2image exist."""
    _ensure_dependencies(
        profile="pdf_ocr",
        packages=(*TESSERACT_APT_PACKAGES, *POPPLER_APT_PACKAGES),
        commands=("tesseract", "pdfinfo", "pdftoppm"),
    )


def _ensure_dependencies(
    *,
    profile: str,
    packages: tuple[str, ...],
    commands: tuple[str, ...],
) -> None:
    if profile in _READY_PROFILES:
        return

    with _INSTALL_LOCK:
        if profile in _READY_PROFILES:
            return
        if _dependencies_present(packages, commands):
            _mark_profile_ready(profile)
            return

        apt_prefix = _apt_command_prefix()
        if not apt_prefix:
            package_list = " ".join(packages)
            raise RuntimeError(
                "Document Query OCR fallback requires system packages "
                f"'{package_list}'. Automatic installation requires apt-get "
                "with root access or non-interactive sudo."
            )

        missing_packages = _missing_apt_packages(packages)
        packages_to_install = missing_packages or list(packages)
        logging.info(
            "Document Query: installing on-demand OCR dependencies: "
            + " ".join(packages_to_install)
        )

        update = _run_apt_command([*apt_prefix, "update"], timeout=300)
        _require_success(update, "refresh apt package metadata")

        install = _run_apt_command(
            [
                *apt_prefix,
                "install",
                "-y",
                "--no-install-recommends",
                *packages_to_install,
            ],
            timeout=900,
        )
        _require_success(install, "install OCR dependencies")

        if not _dependencies_present(packages, commands):
            missing_commands = [
                command for command in commands if shutil.which(command) is None
            ]
            detail = ", ".join(missing_commands) or "required Debian packages"
            raise RuntimeError(
                "Document Query installed OCR dependencies, but they are still "
                f"unavailable: {detail}"
            )

        _mark_profile_ready(profile)


def _mark_profile_ready(profile: str) -> None:
    _READY_PROFILES.add(profile)
    if profile == "pdf_ocr":
        _READY_PROFILES.add("tesseract")


def _dependencies_present(
    packages: tuple[str, ...], commands: tuple[str, ...]
) -> bool:
    return not _missing_apt_packages(packages) and all(
        shutil.which(command) is not None for command in commands
    )


def _missing_apt_packages(packages: tuple[str, ...]) -> list[str]:
    if not shutil.which("dpkg-query"):
        return []

    missing = []
    for package in packages:
        result = subprocess.run(
            ["dpkg-query", "-W", "-f=${Status}", package],
            check=False,
            text=True,
            capture_output=True,
            timeout=8,
        )
        if result.returncode != 0 or "install ok installed" not in result.stdout:
            missing.append(package)
    return missing


def _apt_command_prefix() -> list[str]:
    apt_get = shutil.which("apt-get")
    if not apt_get:
        return []

    get_effective_uid = getattr(os, "geteuid", None)
    if get_effective_uid and get_effective_uid() == 0:
        return [apt_get]

    sudo = shutil.which("sudo")
    if not sudo:
        return []
    env = shutil.which("env") or "env"
    return [sudo, "-n", env, "DEBIAN_FRONTEND=noninteractive", apt_get]


def _run_apt_command(
    command: list[str], *, timeout: int
) -> subprocess.CompletedProcess[str]:
    deadline = time.monotonic() + timeout
    while True:
        result = subprocess.run(command, check=False, text=True, capture_output=True,
                                timeout=max(1, deadline - time.monotonic()),
                                env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"})
        if result.returncode == 0 or "lock" not in (result.stderr or "").lower() or time.monotonic() >= deadline:
            return result
        time.sleep(1)



def _require_success(result: subprocess.CompletedProcess[str], action: str) -> None:
    if result.returncode == 0:
        return
    output = (result.stderr or result.stdout or "apt-get failed").strip()
    raise RuntimeError(f"Document Query could not {action}: {output[-2000:]}")
