import os
import json
import time
import uuid

from python.helpers import files

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "Ov23lirsZNfuBcX2aq3H")
GITHUB_AUTH_FILE = files.get_abs_path("tmp/github_auth.json")

# In-memory store for active device flows.
# Key: flow_id (str), Value: dict with device_code, expires_at, interval.
# Flows are short-lived (~15 min) and Agent Zero is single-user, so in-memory is fine.
_active_flows: dict[str, dict] = {}


def save_github_auth(data: dict):
    """Save GitHub auth data to file."""
    content = json.dumps(data, indent=2)
    files.write_file(GITHUB_AUTH_FILE, content)


def get_github_auth() -> dict | None:
    """Load GitHub auth data from file."""
    if os.path.exists(GITHUB_AUTH_FILE):
        content = files.read_file(GITHUB_AUTH_FILE)
        return json.loads(content)
    return None


def clear_github_auth():
    """Remove GitHub auth file."""
    if os.path.exists(GITHUB_AUTH_FILE):
        os.remove(GITHUB_AUTH_FILE)


def create_flow(device_code: str, expires_in: int, interval: int) -> str:
    """Store a new device flow and return a flow_id."""
    flow_id = uuid.uuid4().hex[:16]
    _active_flows[flow_id] = {
        "device_code": device_code,
        "expires_at": time.time() + expires_in,
        "interval": interval,
    }
    return flow_id


def get_flow(flow_id: str) -> dict | None:
    """Get an active flow by ID, or None if expired/missing."""
    flow = _active_flows.get(flow_id)
    if not flow:
        return None
    if time.time() > flow["expires_at"]:
        _active_flows.pop(flow_id, None)
        return None
    return flow


def remove_flow(flow_id: str):
    """Remove a completed or cancelled flow."""
    _active_flows.pop(flow_id, None)
