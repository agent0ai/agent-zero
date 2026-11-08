"""Retire only replaced runtime dependencies; never touch documents, profiles or login state."""
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys
import psutil
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from helpers import files, runtime, system_packages
from helpers.extension import Extension
from helpers.print_style import PrintStyle

PYTHON_PACKAGES = ('patchright', 'playwright', 'aiogram', 'imapclient', 'exchangelib')
SCRAPER_PACKAGES = {'newspaper3k', 'pyreqwest-impersonate', 'jieba3k', 'feedfinder2',
                    'feedparser', 'feedparser-sgmllib', 'sgmllib3k', 'tinysegmenter',
                    'tldextract', 'requests-file', 'cssselect'}
DESKTOP_PACKAGES = ('libreoffice-*', 'python3-uno', 'xpra*', 'xfce4-*', 'xfwm4', 'xfdesktop4',
                    'thunar*', 'coolwsd*', 'collaboraoffice*')


class RetireOuterFeatures(Extension):
    def execute(self, **kwargs):
        if runtime.is_dockerized():
            retire()


def retire():
    installed = sorted(unused_scrapers())
    for name in PYTHON_PACKAGES:
        try:
            importlib.metadata.version(name)
            installed.append(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    if installed:
        subprocess.run(['uv', 'pip', 'uninstall', '--python', sys.executable, *installed], check=True, timeout=60)
    for relative in ('tmp/playwright', 'usr/plugins/_browser/playwright', 'usr/browser/playwright',
                     'plugins/_whatsapp_integration/whatsapp-bridge/node_modules'):
        path = Path(files.get_abs_path(relative))
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
    if os.geteuid() != 0 or not shutil.which('dpkg-query'):
        return
    # Existing GUI processes may still hold unsaved work during a source-only update.
    for process in psutil.process_iter(['name']):
        if any(part in (process.info.get('name') or '').lower() for part in ('soffice', 'coolwsd', 'xpra', 'xfce', 'xfwm', 'xfdesktop')):
            PrintStyle.warning('Desktop package retirement deferred until old GUI applications are closed and Agent Zero restarts; user files are preserved.')
            return
    result = subprocess.run(['dpkg-query', '-W', '-f=${binary:Package}\t${db:Status-Status}\n', *DESKTOP_PACKAGES],
                            capture_output=True, text=True, timeout=15)
    packages = [line.split('\t')[0] for line in result.stdout.splitlines() if line.endswith('\tinstalled')]
    if packages:
        result = system_packages.run_runtime_apt(['apt-get', 'remove', '-y', *packages], timeout=180)
        if result.returncode:
            raise RuntimeError('Retired Desktop packages could not be removed; retry after resolving APT state')
    # Retain the old owned service declaration as a reversible backup, outside Supervisor's include pattern.
    retire_service(Path('/etc/supervisor/conf.d/a0_office_collabora.conf'))


def unused_scrapers():
    distributions = {canonicalize_name(d.metadata['Name']): d for d in importlib.metadata.distributions()}
    removable = SCRAPER_PACKAGES & distributions.keys()
    # Installed metadata does not record selected extras; conservatively retain their dependencies too.
    while True:
        required = set()
        for name, distribution in distributions.items():
            if name in removable:
                continue
            for declaration in distribution.requires or ():
                requirement = Requirement(declaration)
                required.add(canonicalize_name(requirement.name))
        remaining = removable - required
        if remaining == removable:
            return removable
        removable = remaining


def retire_service(config):
    if config.is_file():
        backup = config.with_suffix('.conf.before-tuxee')
        if not backup.exists():
            shutil.copy2(config, backup)
        config.unlink()
        control = shutil.which('supervisorctl')
        if control:
            try:
                for action in ('reread', 'update'):
                    subprocess.run([control, action], check=True, capture_output=True, timeout=15)
            except Exception:
                shutil.copy2(backup, config)
                raise
