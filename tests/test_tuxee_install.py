"""Official release verification and publication without modifying the host install."""
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from plugins._desktop.helpers import install, runtime


def binary(path, version):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'#!/bin/sh\necho "Tuxee {version}"\n')
    path.chmod(0o755)


@pytest.fixture
def installation(tmp_path, monkeypatch):
    prefix = tmp_path / 'installed'
    target = prefix / 'lib/tuxee/tuxee'
    monkeypatch.setattr(install, 'BINARY', target)
    monkeypatch.setattr(install, 'PREFIX', prefix)
    staged = tmp_path / 'staged'
    binary(staged / 'lib/tuxee/tuxee', '1.4.0')
    (staged / 'lib/tuxee/a0-build-id').write_text('new-recipe')
    support = staged / 'lib/tuxee-audio'
    support.mkdir()
    (support / 'library.so.1').write_text('new library')
    (support / 'library.so').symlink_to('library.so.1')
    return prefix, target, staged


@pytest.mark.parametrize('current,expected', [(None, '1.4.0'), ('0.0.0-a0', '1.4.0'),
                                            ('1.3.0', '1.4.0'), ('1.4.0', '1.4.0'), ('1.5.0', '1.5.0')])
def test_publish_preserves_newer_release_and_uses_standard_layout(installation, current, expected):
    prefix, target, staged = installation
    if current:
        binary(target, current)
        (prefix / 'bin').mkdir()
        (prefix / 'bin/tuxee').symlink_to('../lib/tuxee/tuxee')
    install.publish(staged)
    assert install.binary_version(target) == tuple(map(int, expected.split('.')))
    assert os.readlink(prefix / 'bin/tuxee') == str(target)
    assert (prefix / 'lib/tuxee-audio/library.so').is_symlink()
    assert (prefix / 'lib/tuxee-audio/library.so').read_text() == 'new library'
    assert (target.parent / 'a0-build-id').read_text() == 'new-recipe'


def test_publish_failure_keeps_working_binary_and_marker(installation, monkeypatch):
    prefix, target, staged = installation
    binary(target, '1.3.0')
    marker = target.parent / 'a0-build-id'
    marker.write_text('old-recipe')
    copy = shutil.copy2
    def fail(source, destination, **kwargs):
        if Path(source).name == 'library.so.1':
            raise OSError('fixture copy failed')
        return copy(source, destination, **kwargs)
    monkeypatch.setattr(install.shutil, 'copy2', fail)
    with pytest.raises(OSError, match='fixture copy failed'):
        install.publish(staged)
    assert install.binary_version(target) == (1, 3, 0)
    assert marker.read_text() == 'old-recipe'


def test_publish_honors_official_updater_lock(installation):
    _, target, staged = installation
    binary(target, '1.3.0')
    with (target.parent / '.tuxee-update.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            install.publish(staged)
    assert install.binary_version(target) == (1, 3, 0)
    assert not (target.parent / 'a0-build-id').exists()


@pytest.mark.parametrize('unsafe', ['unknown-version', 'command', 'lock-symlink', 'binary-symlink'])
def test_publish_rejects_unsafe_existing_installation(installation, unsafe):
    prefix, target, staged = installation
    binary(target, 'development' if unsafe == 'unknown-version' else '1.3.0')
    if unsafe == 'command':
        (prefix / 'bin').mkdir()
        (prefix / 'bin/tuxee').write_text('unrelated command')
    elif unsafe == 'lock-symlink':
        (target.parent / '.tuxee-update.lock').symlink_to(target)
    elif unsafe == 'binary-symlink':
        target.rename(target.with_suffix('.original'))
        target.symlink_to(target.with_suffix('.original'))
    with pytest.raises((OSError, RuntimeError)):
        install.publish(staged)
    assert not (target.parent / 'a0-build-id').exists()
    expected = 'development' if unsafe == 'unknown-version' else '1.3.0'
    assert expected in target.read_text()


def test_current_recipe_does_not_reset_independent_update(installation, monkeypatch):
    _, target, _ = installation
    binary(target, '9.0.0')
    (target.parent / 'a0-build-id').write_text(runtime.build_id())
    monkeypatch.setattr(runtime, 'BINARY', target)
    monkeypatch.setattr(install, 'install', lambda: pytest.fail('unexpected rebuild'))
    runtime.ensure_installed()
    assert install.binary_version(target) == (9, 0, 0)


@pytest.mark.parametrize('arch', ['amd64', 'arm64'])
@pytest.mark.parametrize('latest,failure', [
    ('v1.4.0', ''), ('v1.4.1', ''), ('v1.10.0', ''),
    ('v1.4.1', 'checksum'), ('v1.4.1', 'missing'), ('v1.4.1', 'duplicate'),
    ('v1.4.1', 'version'), ('v1.4.1', 'unreleased'), ('v1.3.0', 'too-old'),
    ('v1.4.1-rc.1', 'prerelease'), ('v01.4.1', 'invalid-version'), ('v1.4.1', 'bad-redirect'),
])
def test_release_download_checks_integrity_and_version(tmp_path, arch, latest, failure):
    recipe = tmp_path / 'recipe'
    recipe.mkdir()
    for name in ['release.sh', 'version.txt', 'LICENSE.tuxee']:
        shutil.copy2(runtime.BUILD / name, recipe / name)
    version = latest.removeprefix('v')
    downloads = tmp_path / 'downloads'
    downloads.mkdir()
    asset = 'tuxee-linux-' + arch
    binary(downloads / asset, '0.0.0' if failure == 'version' else version)
    checksum = hashlib.sha256((downloads / asset).read_bytes()).hexdigest()
    entry = f'{checksum}  {asset}\n'
    sums = {'checksum': f'{"0" * 64}  {asset}\n', 'missing': '', 'duplicate': entry * 2}.get(failure, entry)
    (downloads / 'checksums.txt').write_text(sums)
    commands = tmp_path / 'bin'
    commands.mkdir()
    (commands / 'curl').write_text('''#!/bin/sh
set -eu
test "$FAILURE" != unreleased || exit 22
for argument in "$@"; do
    if [ "$argument" = https://github.com/agent0ai/tuxee/releases/latest ]; then
        printf '%s' "$LATEST_URL"
        exit 0
    fi
done
while [ "$1" != -o ]; do url="$1"; shift; done
test "$url" = "https://github.com/agent0ai/tuxee/releases/download/$LATEST/${url##*/}"
cp "$DOWNLOADS/${url##*/}" "$2"
''')
    (commands / 'dpkg').write_text(f'#!/bin/sh\necho {arch}\n')
    for path in commands.iterdir():
        path.chmod(0o755)
    output = tmp_path / 'output'
    env = {**os.environ, 'PATH': str(commands) + ':' + os.environ['PATH'],
           'DOWNLOADS': str(downloads), 'FAILURE': failure, 'LATEST': latest,
           'LATEST_URL': ('https://example.invalid/' if failure == 'bad-redirect' else
                          'https://github.com/agent0ai/tuxee/releases/tag/') + latest}
    result = subprocess.run(['sh', str(recipe / 'release.sh'), str(output)], env=env, capture_output=True)
    target = output / 'usr/local/lib/tuxee/tuxee'
    if failure:
        assert result.returncode != 0
        assert not target.exists()
    else:
        assert result.returncode == 0, result.stderr.decode()
        assert target.read_bytes() == (downloads / asset).read_bytes()
        assert not (output / 'usr/local/bin/tuxee').exists()
