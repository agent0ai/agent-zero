"""Shared synthetic bridge fixtures; never installs a runtime or grants access."""
from copy import deepcopy
from pathlib import Path
import re
import shutil
import subprocess

WEBUI = Path(__file__).resolve().parents[1] / "plugins/_browser/webui"


def run_node(script):
    if not shutil.which("node"):
        import pytest
        pytest.skip("Node required")
    result = subprocess.run(["node", "--input-type=module"], input=script,
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr


def run_model(filename, script):
    source = (WEBUI / filename).read_text().split("export const store =", 1)[0]
    source = re.sub(r"^import .*;\n", "", source, flags=re.M)
    source = source.replace("export function ", "function ")
    source = source.replace("export async function ", "async function ")
    run_node(source + "\n" + script)


class MemoryPersistence:
    def __init__(self):
        self.value = None

    def load(self):
        return deepcopy(self.value)

    def save(self, value):
        self.value = deepcopy(value)


class MemoryKeyValue:
    """KVP-shaped storage: preserve the exact default sentinel on a miss."""
    def __init__(self):
        self.value = {}

    def load(self, key, default=None):
        return deepcopy(self.value[key]) if key in self.value else default

    def save(self, key, value):
        self.value[key] = deepcopy(value)


class FakeApiHandler:
    """Endpoint-unit-test base only; shared middleware security is tested separately."""
    def __init__(self, *_args, **_kwargs):
        pass

    @classmethod
    def requires_auth(cls):
        return True

    @classmethod
    def requires_csrf(cls):
        return cls.requires_auth()


class FakeResponse:
    def __init__(self, *, response, status, mimetype, headers):
        self.response = response
        self.status = status
        self.mimetype = mimetype
        self.headers = headers
