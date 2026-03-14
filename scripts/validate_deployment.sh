#!/bin/bash
# Validate all Agent Jumbo customizations deployed to Docker
# Run this script to verify all custom features are properly deployed

set -e

CONTAINER="${CONTAINER:-agent-jumbo}"
BASE_URL="${BASE_URL:-http://localhost:50080}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() { echo -e "${GREEN}✅ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo "=========================================="
echo " Agent Jumbo Docker Deployment Validation"
echo "=========================================="
echo ""

# 1. Check container running
echo "=== Container Status ==="
if docker ps --filter name=$CONTAINER --format "{{.Status}}" | grep -q "Up"; then
    STATUS=$(docker ps --filter name=$CONTAINER --format "{{.Status}}")
    pass "Container running: $STATUS"
else
    fail "Container not running"
    exit 1
fi
echo ""

# 2. Check custom instruments (17 modules)
echo "=== Custom Instruments (17 modules) ==="
INSTRUMENTS=(
    "ai_migration"
    "business_xray"
    "claude_sdk"
    "customer_lifecycle"
    "deployment_orchestrator"
    "diagram_architect"
    "diagram_generator"
    "plugin_marketplace"
    "portfolio_manager"
    "project_scaffold"
    "property_manager"
    "ralph_loop"
    "sales_generator"
    "skill_importer"
    "virtual_team"
    "workflow_engine"
    "scheduler"
)

INST_PASS=0
INST_FAIL=0
for mod in "${INSTRUMENTS[@]}"; do
    if docker exec $CONTAINER test -d /a0/instruments/custom/$mod 2>/dev/null; then
        pass "$mod"
        ((INST_PASS++))
    else
        fail "$mod MISSING"
        ((INST_FAIL++))
    fi
done
echo "Instruments: $INST_PASS passed, $INST_FAIL failed"
echo ""

# 3. Check custom tools (18 tools)
echo "=== Custom Tools (18 tools) ==="
TOOLS=(
    "skill_importer"
    "project_scaffold"
    "ai_migration"
    "diagram_architect"
    "sales_generator"
    "deployment_orchestrator"
    "plugin_marketplace"
    "claude_sdk_bridge"
    "email"
    "email_advanced"
    "customer_lifecycle"
    "virtual_team"
    "business_xray_tool"
    "portfolio_manager_tool"
    "property_manager_tool"
    "workflow_engine"
    "workflow_training"
    "ralph_loop"
)

TOOL_PASS=0
TOOL_FAIL=0
for tool in "${TOOLS[@]}"; do
    if docker exec $CONTAINER test -f /a0/python/tools/${tool}.py 2>/dev/null; then
        pass "$tool"
        ((TOOL_PASS++))
    else
        fail "$tool MISSING"
        ((TOOL_FAIL++))
    fi
done
echo "Tools: $TOOL_PASS passed, $TOOL_FAIL failed"
echo ""

# 4. Check custom APIs (31 endpoints)
echo "=== Custom API Endpoints (31 endpoints) ==="
APIS=(
    # Gmail
    "gmail_oauth_start"
    "gmail_oauth_callback"
    "gmail_accounts_list"
    "gmail_account_remove"
    "gmail_test_send"
    # Cowork
    "cowork_approvals_list"
    "cowork_approvals_update"
    "cowork_folders_get"
    "cowork_folders_set"
    # Workflow
    "workflow_get"
    "workflow_save"
    "workflow_clear"
    "workflow_engine_api"
    "workflow_training_api"
    "workflow_dashboard"
    # Telemetry
    "telemetry_get"
    "telemetry_clear"
    # Ralph Loop
    "ralph_loop_control"
    "ralph_loop_dashboard"
    # Scheduler
    "scheduler_task_create"
    "scheduler_task_update"
    "scheduler_task_delete"
    "scheduler_task_run"
    "scheduler_tasks_list"
    "scheduler_tick"
    # Other
    "prompt_enhance_get"
    "csrf_token"
)

API_PASS=0
API_FAIL=0
for api in "${APIS[@]}"; do
    if docker exec $CONTAINER test -f /a0/python/api/${api}.py 2>/dev/null; then
        pass "$api"
        ((API_PASS++))
    else
        fail "$api MISSING"
        ((API_FAIL++))
    fi
done
echo "APIs: $API_PASS passed, $API_FAIL failed"
echo ""

# 5. Check custom extensions (6 extensions)
echo "=== Custom Extensions (6 extensions) ==="
EXTENSIONS=(
    "message_loop_prompts_after/_80_prompt_enhancer.py"
    "system_prompt/_30_cowork_prompt.py"
    "tool_execute_after/_30_telemetry_end.py"
    "tool_execute_before/_20_cowork_approvals.py"
    "tool_execute_before/_30_telemetry_start.py"
    "message_loop_prompts_after/_85_ralph_loop_check.py"
)

EXT_PASS=0
EXT_FAIL=0
for ext in "${EXTENSIONS[@]}"; do
    if docker exec $CONTAINER test -f /a0/python/extensions/${ext} 2>/dev/null; then
        pass "$(basename $ext)"
        ((EXT_PASS++))
    else
        fail "$(basename $ext) MISSING"
        ((EXT_FAIL++))
    fi
done
echo "Extensions: $EXT_PASS passed, $EXT_FAIL failed"
echo ""

# 6. Check custom helpers (9 helpers)
echo "=== Custom Helpers (9 helpers) ==="
HELPERS=(
    "cowork.py"
    "db_manager.py"
    "email_sender.py"
    "gmail_api_client.py"
    "gmail_oauth2.py"
    "gmail_push_notifications.py"
    "master_orchestrator.py"
    "telemetry.py"
    "observability_adapters.py"
)

HELP_PASS=0
HELP_FAIL=0
for helper in "${HELPERS[@]}"; do
    if docker exec $CONTAINER test -f /a0/python/helpers/${helper} 2>/dev/null; then
        pass "$helper"
        ((HELP_PASS++))
    else
        fail "$helper MISSING"
        ((HELP_FAIL++))
    fi
done
echo "Helpers: $HELP_PASS passed, $HELP_FAIL failed"
echo ""

# 7. Check UI components
echo "=== UI Components ==="
UI_COMPONENTS=(
    "settings/workflow"
    "settings/ralph-loop"
    "settings/observability"
    "settings/cowork"
    "settings/external"
    "settings/prompt"
    "modals/file-browser"
)

UI_PASS=0
UI_FAIL=0
for comp in "${UI_COMPONENTS[@]}"; do
    if docker exec $CONTAINER test -d /a0/webui/components/${comp} 2>/dev/null; then
        pass "$comp"
        ((UI_PASS++))
    else
        fail "$comp MISSING"
        ((UI_FAIL++))
    fi
done
echo "UI Components: $UI_PASS passed, $UI_FAIL failed"
echo ""

# 8. Test API endpoints (live)
echo "=== API Health Checks (Live Tests) ==="

# Get CSRF token first
echo -n "Getting CSRF token... "
CSRF_RESP=$(curl -s -c /tmp/cookies.txt -H "Origin: $BASE_URL" "$BASE_URL/csrf_token" 2>/dev/null || echo "")
if echo "$CSRF_RESP" | grep -q '"token"'; then
    CSRF=$(echo "$CSRF_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || echo "")
    if [ -n "$CSRF" ]; then
        pass "Got CSRF token"
    else
        warn "Could not parse CSRF token"
    fi
else
    warn "Could not get CSRF token - API tests may fail"
    CSRF=""
fi

# Test Ralph Loop Dashboard API
echo -n "Testing Ralph Loop Dashboard API... "
RESP=$(curl -s -X POST "$BASE_URL/ralph_loop_dashboard" \
    -H "Content-Type: application/json" \
    -H "Origin: $BASE_URL" \
    -H "X-CSRF-Token: $CSRF" \
    -b /tmp/cookies.txt \
    -d '{}' 2>/dev/null || echo "")
if echo "$RESP" | grep -q '"success"'; then
    pass "Ralph Loop Dashboard API"
else
    fail "Ralph Loop Dashboard API"
fi

# Test Workflow Dashboard API
echo -n "Testing Workflow Dashboard API... "
RESP=$(curl -s -X POST "$BASE_URL/workflow_dashboard" \
    -H "Content-Type: application/json" \
    -H "Origin: $BASE_URL" \
    -H "X-CSRF-Token: $CSRF" \
    -b /tmp/cookies.txt \
    -d '{}' 2>/dev/null || echo "")
if echo "$RESP" | grep -q '"success"'; then
    pass "Workflow Dashboard API"
else
    fail "Workflow Dashboard API"
fi

# Test Telemetry API
echo -n "Testing Telemetry API... "
RESP=$(curl -s -X POST "$BASE_URL/telemetry_get" \
    -H "Content-Type: application/json" \
    -H "Origin: $BASE_URL" \
    -H "X-CSRF-Token: $CSRF" \
    -b /tmp/cookies.txt \
    -d '{}' 2>/dev/null || echo "")
if echo "$RESP" | grep -q '"success"'; then
    pass "Telemetry API"
else
    fail "Telemetry API"
fi

# Test Web UI
echo -n "Testing Web UI accessibility... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    pass "Web UI (HTTP $HTTP_CODE)"
else
    fail "Web UI (HTTP $HTTP_CODE)"
fi

echo ""

# 9. Summary
echo "=========================================="
echo " Deployment Validation Summary"
echo "=========================================="
TOTAL_PASS=$((INST_PASS + TOOL_PASS + API_PASS + EXT_PASS + HELP_PASS + UI_PASS))
TOTAL_FAIL=$((INST_FAIL + TOOL_FAIL + API_FAIL + EXT_FAIL + HELP_FAIL + UI_FAIL))
TOTAL=$((TOTAL_PASS + TOTAL_FAIL))

echo ""
echo "Total Checks: $TOTAL"
echo -e "${GREEN}Passed: $TOTAL_PASS${NC}"
if [ $TOTAL_FAIL -gt 0 ]; then
    echo -e "${RED}Failed: $TOTAL_FAIL${NC}"
else
    echo -e "Failed: 0"
fi

echo ""
if [ $TOTAL_FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All validations passed! Deployment is complete.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some validations failed. Review the output above.${NC}"
    exit 1
fi
