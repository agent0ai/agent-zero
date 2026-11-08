"""Guest-only, serialized file RPC. The host mounts /request read-only."""
import json
from pathlib import Path
import runpy
import time

state = Path('/var/lib/a0-worker')
handler = runpy.run_path('/plugin/sandbox/worker.py')['handle']


def write(name, payload):
    temporary = state / (name + '.tmp')
    temporary.write_text(json.dumps(payload), encoding='utf-8')
    temporary.replace(state / name)


write('ready.json', {'boot': json.loads(Path('/request/request.json').read_text()).get('boot')})
last_id = None
while True:
    try:
        request = json.loads(Path('/request/request.json').read_text())
    except (OSError, ValueError):
        request = {}
    request_id = request.get('id')
    if not request_id and last_id:
        (state / 'response.json').unlink(missing_ok=True)
        write('ack.json', {'id': last_id})
        last_id = None
    if request_id and request_id != last_id:
        last_id = request_id
        try:
            response = {'result': handler(request['payload'])}
        except Exception as exc:
            response = {'error': f'{type(exc).__name__}: {exc}'}
        write('response.json', {'id': request_id, **response})
    time.sleep(.05)
