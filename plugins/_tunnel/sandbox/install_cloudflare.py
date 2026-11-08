"""Install the official native cloudflared binary inside the sandbox."""
import hashlib
import json
import os
from pathlib import Path
import platform
import urllib.request


def install():
    target = Path('/opt/a0-tunnel/cloudflared')
    if target.is_file() and os.access(target, os.X_OK):
        return
    arch = {'x86_64': 'amd64', 'aarch64': 'arm64'}.get(platform.machine())
    if not arch:
        raise RuntimeError('Cloudflare installer supports Linux amd64 and arm64')
    request = urllib.request.Request(
        'https://api.github.com/repos/cloudflare/cloudflared/releases/latest',
        headers={'User-Agent': 'agent-zero-tunnel'},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        release = json.load(response)
    asset = next(item for item in release['assets'] if item['name'] == f'cloudflared-linux-{arch}')
    expected = asset.get('digest', '')
    if not expected.startswith('sha256:'):
        raise RuntimeError('Cloudflare release does not provide a SHA-256 digest')
    temporary = target.with_suffix('.download')
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(asset['browser_download_url'], timeout=60) as response, temporary.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != expected.removeprefix('sha256:'):
            raise RuntimeError('Cloudflare binary checksum mismatch')
        temporary.chmod(0o755)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    install()
