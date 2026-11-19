"""Preserve pre-scope Telegram settings before the new lifecycle reads them."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import tempfile

from helpers import files, plugins
from plugins._telegram_integration.helpers.constants import PLUGIN_NAME, STATE_FILE

BACKUP_DIR = "usr/plugins/_telegram_integration/backups/config-scopes-v1"


def prepare_upgrade() -> None:
    """Back up old settings and upgrade legacy webhook secrets without resetting bots."""
    root = Path(files.get_abs_path(BACKUP_DIR))
    manifest = root / "manifest.json"
    completed = root / "complete.json"
    if completed.is_file():
        return
    sources = {entry["path"] for pattern in (plugins.CONFIG_FILE_NAME, plugins.TOGGLE_FILE_PATTERN)
               for entry in plugins.find_plugin_assets(pattern, plugin_name=PLUGIN_NAME)}
    state = files.get_abs_path(STATE_FILE)
    if Path(state).is_file():
        sources.add(state)
    if not sources:
        return
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root.chmod(0o700)
    if not manifest.is_file():
        entries = []
        for source in sorted(sources):
            path = Path(source)
            data = path.read_bytes()
            relative = files.deabsolute_path(str(path))
            digest = hashlib.sha256(data).hexdigest()
            filename = hashlib.sha256(relative.encode()).hexdigest() + ".backup"
            _write_private(root / filename, data)
            entries.append({"path": relative, "backup": filename, "sha256": digest})
        _write_private(manifest, json.dumps({"version": 1, "files": entries}, indent=2).encode())
    backed_up = {entry["path"] for entry in json.loads(manifest.read_text())["files"]}
    for source in sorted(sources):
        path = Path(source)
        if path.name != plugins.CONFIG_FILE_NAME or files.deabsolute_path(source) not in backed_up:
            continue
        config = json.loads(path.read_bytes())
        changed = False
        for bot in config.get("bots", []):
            secret = bot.get("webhook_secret", "")
            if bot.get("mode") == "webhook" and (not isinstance(secret, str) or not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", secret)):
                bot["webhook_secret"] = secrets.token_urlsafe(32)
                changed = True
        if changed:
            # Resolve a symlink so upgrading its contents preserves the user's link.
            _write_private(path.resolve(), json.dumps(config, indent=2).encode())
    # Partial migrations retry without rotating a secret that was already upgraded.
    _write_private(completed, b'{"version": 1}\n')


def _write_private(path: Path, data: bytes) -> None:
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".upgrade-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
