#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STACK_FILE="${STACK_FILE:-$ROOT_DIR/docker/swarm/agent-zero-stack.yml}"
STACK_NAME="${STACK_NAME:-agent-zero}"
ACTION="${1:-deploy}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [deploy|status|remove]

Environment variables:
  STACK_NAME                  Swarm stack name (default: agent-zero)
  STACK_FILE                  Stack file path (default: docker/swarm/agent-zero-stack.yml)
  AGENT_ZERO_IMAGE            Container image (default: frdel/agent-zero-run:latest)
  AGENT_ZERO_PUBLISHED_PORT   Host port for Web UI (default: 5000)
  AGENT_ZERO_REPLICAS         Number of replicas (default: 1)
  SWARM_ADVERTISE_ADDR        Optional address for 'docker swarm init --advertise-addr'
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

ensure_swarm() {
  local state
  state="$(docker info --format '{{.Swarm.LocalNodeState}}')"
  if [[ "$state" == "active" ]]; then
    return
  fi

  echo "Docker Swarm is not active. Initializing..."
  if [[ -n "${SWARM_ADVERTISE_ADDR:-}" ]]; then
    docker swarm init --advertise-addr "$SWARM_ADVERTISE_ADDR"
  else
    docker swarm init
  fi
}

deploy_stack() {
  ensure_swarm

  if [[ ! -f "$STACK_FILE" ]]; then
    echo "Stack file not found: $STACK_FILE"
    exit 1
  fi

  docker stack deploy -c "$STACK_FILE" "$STACK_NAME"

  echo
  docker stack services "$STACK_NAME"
  echo
  echo "Agent Zero should be reachable at:"
  echo "  http://<swarm-node-ip>:${AGENT_ZERO_PUBLISHED_PORT:-5000}"
}

status_stack() {
  docker stack services "$STACK_NAME"
  echo
  docker service ps "${STACK_NAME}_agent-zero"
}

remove_stack() {
  docker stack rm "$STACK_NAME"
}

require_cmd docker

case "$ACTION" in
  deploy)
    deploy_stack
    ;;
  status)
    status_stack
    ;;
  remove)
    remove_stack
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
