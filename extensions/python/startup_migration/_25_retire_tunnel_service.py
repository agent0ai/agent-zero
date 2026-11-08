"""Retire the image-owned controller on source-only upgrades too."""
from pathlib import Path
import os
import re
import shutil
import subprocess

from helpers.extension import Extension
from helpers import runtime


class RetireTunnelController(Extension):
    def execute(self, **kwargs):
        if runtime.is_dockerized():
            retire()


def retire(config: Path = Path('/etc/supervisor/conf.d/supervisord.conf')) -> bool:
    control = shutil.which('supervisorctl')
    if control is None or not config.is_file():
        return False
    original = config.read_text()
    pattern = r'(?ms)^\[program:run_tunnel_api\]\n.*?(?=^\[|\Z)'
    section = re.search(pattern, original)
    if not section or 'command=/exe/run_tunnel_api.sh' not in section.group():
        return False
    backup = config.with_name(config.name + '.before-tunnel-plugin')
    if not backup.exists():
        shutil.copy2(config, backup)
    temporary = config.with_name(config.name + '.tunnel-migration')
    temporary.write_text(re.sub(pattern, '', original))
    shutil.copymode(config, temporary)
    os.replace(temporary, config)
    # update stops and removes the old process group without touching WebUI.
    try:
        for action in ('reread', 'update'):
            subprocess.run([control, action], check=True, capture_output=True, text=True, timeout=15)
    except Exception:
        temporary.write_text(original)
        shutil.copymode(config, temporary)
        os.replace(temporary, config)
        raise
    return True
