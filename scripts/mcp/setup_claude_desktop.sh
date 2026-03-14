#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-agent-jumbo}"
CLAUDE_CONFIG_PATH="${CLAUDE_CONFIG_PATH:-$HOME/.config/Claude/claude_desktop_config.json}"
SERVER_NAME="${SERVER_NAME:-agent-jumbo-local}"
A0_BASE_URL="${A0_BASE_URL:-http://localhost:50080}"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
  if docker ps --format '{{.Names}}' | grep -qx "agent-zero"; then
    CONTAINER_NAME="agent-zero"
  else
    echo "Container '$CONTAINER_NAME' is not running."
    exit 1
  fi
fi

# Prefer the live token used by the running UI instance.
TOKEN=""
LIVE_MSG="$(curl -sS "$A0_BASE_URL/mcp/t-foo/sse" --max-time 4 || true)"
if [[ "$LIVE_MSG" == *"expected_token="* ]]; then
  TOKEN="${LIVE_MSG##*expected_token=}"
fi

# Fallback: read from container settings if live probe is unavailable.
if [[ -z "$TOKEN" ]]; then
  TOKEN="$(docker exec "$CONTAINER_NAME" bash -lc 'cd /a0 && . /ins/setup_venv.sh local >/dev/null 2>&1 && python -c "from python.helpers import settings; print(settings.get_settings().get(\"mcp_server_token\", \"\"))"' | tr -d '\r')"
fi

if [[ -z "$TOKEN" ]]; then
  echo "Could not read mcp_server_token from container '$CONTAINER_NAME'."
  exit 1
fi

SSE_URL="$A0_BASE_URL/mcp/t-$TOKEN/sse"

mkdir -p "$(dirname "$CLAUDE_CONFIG_PATH")"
if [[ ! -f "$CLAUDE_CONFIG_PATH" ]]; then
  echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG_PATH"
fi

python3 - "$CLAUDE_CONFIG_PATH" "$SERVER_NAME" "$SSE_URL" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
server_name = sys.argv[2]
sse_url = sys.argv[3]

raw = path.read_text(encoding="utf-8").strip() or "{}"
try:
    cfg = json.loads(raw)
except Exception:
    cfg = {}

if not isinstance(cfg, dict):
    cfg = {}

mcp = cfg.get("mcpServers")
if not isinstance(mcp, dict):
    mcp = {}

mcp[server_name] = {
    "command": "npx",
    "args": ["-y", "mcp-remote", sse_url]
}

cfg["mcpServers"] = mcp
path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
PY

echo "Updated Claude Desktop config: $CLAUDE_CONFIG_PATH"
echo "Server entry: $SERVER_NAME"
echo "SSE URL: $SSE_URL"
echo "Restart Claude Desktop to load the MCP server."
