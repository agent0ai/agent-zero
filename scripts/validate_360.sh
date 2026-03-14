#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-quick}"
BASE_URL="${BASE_URL:-http://localhost:50080}"
REPORT_DIR="${REPORT_DIR:-$ROOT_DIR/artifacts/validation}"
TS="$(date +%Y%m%d-%H%M%S)"
REPORT_FILE="$REPORT_DIR/validation-360-$TS.log"

mkdir -p "$REPORT_DIR"

PASS=0
FAIL=0

log() {
  echo "$1" | tee -a "$REPORT_FILE"
}

run_check() {
  local name="$1"
  shift
  log "[CHECK] $name"
  if "$@" >>"$REPORT_FILE" 2>&1; then
    log "[PASS] $name"
    PASS=$((PASS + 1))
  else
    log "[FAIL] $name"
    FAIL=$((FAIL + 1))
  fi
  log ""
}

check_endpoint_json() {
  local endpoint="$1"
  local required_key="$2"
  local out
  out="$(curl -fsS -m 12 "$BASE_URL$endpoint")"
  python - <<'PY' "$out" "$required_key"
import json, sys
payload = json.loads(sys.argv[1])
key = sys.argv[2]
if key and key not in payload:
    raise SystemExit(f"missing key: {key}")
print("ok")
PY
}

check_chat_roundtrip() {
  local create_payload='{}'
  local ctx_json ctxid send_json poll_json i

  ctx_json="$(curl -fsS -m 12 -H 'Content-Type: application/json' -X POST "$BASE_URL/chat_create" -d "$create_payload")"
  ctxid="$(python - <<'PY' "$ctx_json"
import json, sys
print(json.loads(sys.argv[1]).get("ctxid", ""))
PY
)"

  if [[ -z "$ctxid" ]]; then
    echo "missing ctxid"
    return 1
  fi

  send_json="$(curl -fsS -m 20 -H 'Content-Type: application/json' -X POST "$BASE_URL/message_async" -d "{\"text\":\"validation 360 smoke ping\",\"context\":\"$ctxid\"}")"
  python - <<'PY' "$send_json"
import json, sys
payload = json.loads(sys.argv[1])
if payload.get("message") != "Message received.":
    raise SystemExit(f"unexpected message_async response: {payload}")
PY

  for i in $(seq 1 35); do
    poll_json="$(curl -fsS -m 12 -H 'Content-Type: application/json' -X POST "$BASE_URL/poll" -d "{\"context\":\"$ctxid\",\"log_from\":0,\"notifications_from\":0}")"
    if python - <<'PY' "$poll_json"
import json, sys
p = json.loads(sys.argv[1])
if p.get("context") and p.get("log_version", 0) >= 2 and p.get("log_progress_active") is False:
    raise SystemExit(0)
raise SystemExit(1)
PY
    then
      return 0
    fi
    sleep 1
  done

  echo "poll did not settle within timeout"
  return 1
}

check_skills_discovery() {
  local payload
  payload="$(curl -fsS -m 12 -H 'Content-Type: application/json' -X POST "$BASE_URL/skills_list" -d '{}')"
  python - <<'PY' "$payload"
import json, sys
skills = json.loads(sys.argv[1]).get("skills", [])
if not isinstance(skills, list):
    raise SystemExit("skills is not a list")
if len(skills) == 0:
    raise SystemExit("no skills discovered")
print(f"skills={len(skills)}")
PY
}

log "Validation 360"
log "mode=$MODE base_url=$BASE_URL report=$REPORT_FILE"
log ""

run_check "python compile core files" python -m py_compile \
  "$ROOT_DIR/python/helpers/tool.py" \
  "$ROOT_DIR/python/api/message.py" \
  "$ROOT_DIR/python/api/message_async.py" \
  "$ROOT_DIR/python/helpers/skill_registry.py"

run_check "tool constructor contract test" pytest -q "$ROOT_DIR/tests/test_tool_constructor_contract.py"
run_check "sensitive token redaction test" pytest -q "$ROOT_DIR/tests/test_sensitive_token_redaction.py"
run_check "mcp tools cache tests" pytest -q "$ROOT_DIR/tests/test_mcp_tools_cache.py" "$ROOT_DIR/tests/test_mcp_tools_reload_api.py"
run_check "project lifecycle/validation tests" pytest -q "$ROOT_DIR/tests/test_project_validation.py" "$ROOT_DIR/tests/test_project_lifecycle.py"
run_check "context persistence restart compatibility" pytest -q "$ROOT_DIR/tests/test_telegram_bridge_restart_persistence.py"

run_check "api health endpoint" check_endpoint_json "/health" "gitinfo"
run_check "api chat readiness" check_endpoint_json "/chat_readiness" "ready"
run_check "api chat roundtrip" check_chat_roundtrip
run_check "api skills discovery" check_skills_discovery

if [[ "$MODE" == "full" ]]; then
  run_check "extended integration subset" pytest -q \
    "$ROOT_DIR/tests/test_mahoosuc_e2e.py" \
    "$ROOT_DIR/tests/test_mahoosuc_native_tools.py" \
    "$ROOT_DIR/tests/test_workflow_api.py"
fi

log "Summary: pass=$PASS fail=$FAIL"
log "Report: $REPORT_FILE"

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
