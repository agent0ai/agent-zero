import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _get_named_exports(source: str) -> set[str]:
    exports: set[str] = set()

    exports.update(re.findall(r"^export\s+function\s+([A-Za-z0-9_]+)\s*\(", source, flags=re.M))
    exports.update(re.findall(r"^export\s+const\s+([A-Za-z0-9_]+)\s*=", source, flags=re.M))
    exports.update(re.findall(r"^export\s+class\s+([A-Za-z0-9_]+)\s*[\{:]", source, flags=re.M))

    for m in re.findall(r"^export\s*\{([^}]+)\}\s*;?", source, flags=re.M):
        for item in m.split(","):
            item = item.strip()
            if not item:
                continue
            # Handle: `foo as bar`
            parts = item.split()
            if len(parts) >= 3 and parts[-2] == "as":
                exports.add(parts[-1])
            else:
                exports.add(parts[0])

    return exports


def test_websocket_js_exports_minimal_namespaced_api_surface() -> None:
    source = (PROJECT_ROOT / "webui" / "js" / "websocket.js").read_text(encoding="utf-8")
    exports = _get_named_exports(source)

    assert "createNamespacedClient" in exports
    assert "getNamespacedClient" in exports

    assert "broadcast" not in exports
    assert "requestAll" not in exports
