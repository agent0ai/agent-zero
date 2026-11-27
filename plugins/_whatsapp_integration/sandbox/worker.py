"""Own the Baileys process and dependencies inside the persistent guest."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request

bridge = None
runtime = Path('/opt/whatsapp')


def install():
    source = Path('/plugin/whatsapp-bridge')
    fingerprint = hashlib.sha256(b''.join((source / name).read_bytes() for name in
                                         ('package.json', 'package-lock.json'))).hexdigest()
    runtime.mkdir(exist_ok=True)
    marker = runtime / '.installed'
    for item in source.iterdir():
        if item.is_file():
            shutil.copyfile(item, runtime / item.name)
    if not marker.exists() or marker.read_text() != fingerprint or not (runtime / 'node_modules/@whiskeysockets/baileys/package.json').is_file():
        marker.unlink(missing_ok=True)
        with open('/var/lib/a0-worker/install.log', 'ab') as log:
            subprocess.run(['npm', 'ci', '--omit=dev', '--no-audit', '--no-fund'],
                           cwd=runtime, stdout=log, stderr=log, check=True, timeout=900)
        marker.write_text(fingerprint)


def handle(payload):
    global bridge
    action = payload['action']
    if action == 'status':
        return bridge is not None and bridge.poll() is None
    if action != 'start':
        raise ValueError('Unsupported WhatsApp worker action')
    if bridge and bridge.poll() is None:
        bridge.terminate()
        try:
            bridge.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bridge.kill()
            bridge.wait(timeout=5)
    install()
    config = payload['config']
    command = ['node', str(runtime / 'bridge.js')]
    for key, value in config.items():
        command.extend(['--' + key, str(value)])
    # Never inherit Agent Zero credentials; the token authorizes only this bridge.
    env = {**os.environ, 'A0_BRIDGE_TOKEN': payload['token']}
    with open('/var/lib/a0-worker/bridge.log', 'ab') as log:
        bridge = subprocess.Popen(command, cwd=runtime, env=env, stdout=log, stderr=log)
    url = f"http://127.0.0.1:{int(config['port'])}/health"
    for _ in range(40):
        if bridge.poll() is not None:
            raise RuntimeError('WhatsApp bridge exited; inspect its private sandbox log')
        try:
            request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + payload['token']})
            with urllib.request.urlopen(request, timeout=.5) as response:
                if response.status == 200:
                    return True
        except OSError:
            pass
        time.sleep(.25)
    bridge.terminate()
    raise RuntimeError('WhatsApp bridge did not become ready')
