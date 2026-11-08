"""Guest installer progress, scoped to the current worker boot request."""
import json
from pathlib import Path
import sys
import time

state = Path('/var/lib/a0-worker')
request = json.loads(Path('/request/request.json').read_text())
payload = {'boot': request.get('boot'), 'stage': sys.argv[1],
           'message': sys.argv[2], 'updated_at': time.time()}
temporary = state / 'progress.tmp'
temporary.write_text(json.dumps(payload))
temporary.replace(state / 'progress.json')
