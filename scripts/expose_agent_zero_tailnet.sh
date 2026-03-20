#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-up}"
AGENT_ZERO_PORT="${AGENT_ZERO_PUBLISHED_PORT:-5000}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [up|down|status]

Environment variables:
  AGENT_ZERO_PUBLISHED_PORT   Agent Zero host port to expose (default: 5000)
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

tailnet_url() {
  tailscale status --json 2>/dev/null | python3 -c \
    'import json,sys; d=json.load(sys.stdin); n=d.get("Self",{}).get("DNSName","").rstrip("."); print(f"https://{n}" if n else "")'
}

check_tailscale() {
  require_cmd tailscale
  require_cmd python3

  if ! tailscale status >/dev/null 2>&1; then
    echo "Tailscale is not connected. Run 'tailscale up' first."
    exit 1
  fi
}

up() {
  check_tailscale
  tailscale serve --bg http / "http://127.0.0.1:${AGENT_ZERO_PORT}"
  local url
  url="$(tailnet_url || true)"
  echo "Tailnet serve enabled -> http://127.0.0.1:${AGENT_ZERO_PORT}"
  if [[ -n "$url" ]]; then
    echo "Open Agent Zero on your tailnet at:"
    echo "  $url"
  fi
}

down() {
  check_tailscale
  tailscale serve reset
  echo "Tailnet serve rules removed."
}

status() {
  check_tailscale
  tailscale serve status
}

case "$ACTION" in
  up)
    up
    ;;
  down)
    down
    ;;
  status)
    status
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown action: $ACTION"
    usage
    exit 1
    ;;
esac
