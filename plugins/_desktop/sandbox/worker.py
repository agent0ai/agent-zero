"""Build an existing-install upgrade with the same recipe as the Docker image."""
import base64
from pathlib import Path
import subprocess
import tempfile


def handle(payload):
    if payload != {'action': 'build'}:
        raise ValueError('Unsupported Tuxee build operation')
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / 'output'
        with open('/var/lib/a0-worker/build.log', 'wb') as log:
            subprocess.run(['sh', '/plugin/build/build.sh', str(output)], check=True, stdout=log, stderr=log, timeout=1500)
        archive = Path(directory) / 'runtime.tar.gz'
        subprocess.run(['tar', '-czf', str(archive), '-C', str(output), '.'], check=True)
        return base64.b64encode(archive.read_bytes()).decode()
