#!/bin/bash
# Test LLM Router APIs
# Usage: ./scripts/test_llm_router_apis.sh [base_url]

BASE_URL="${1:-http://localhost:50080}"
echo "=== LLM Router API Tests ==="
echo "Base URL: $BASE_URL"
echo ""

# Get CSRF token
echo "Getting CSRF token..."
CSRF_RESPONSE=$(curl -s -c /tmp/cookies.txt -H "Origin: $BASE_URL" "$BASE_URL/csrf_token")
CSRF=$(echo "$CSRF_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

if [ -z "$CSRF" ]; then
    echo "❌ Failed to get CSRF token"
    echo "Response: $CSRF_RESPONSE"
    exit 1
fi
echo "✅ CSRF Token: ${CSRF:0:20}..."
echo ""

# Helper function to test an endpoint
test_endpoint() {
    local endpoint="$1"
    local data="$2"
    local expected="$3"

    echo "Testing: $endpoint"
    RESPONSE=$(curl -s -X POST "$BASE_URL/$endpoint" \
        -H "Content-Type: application/json" \
        -H "Origin: $BASE_URL" \
        -H "X-CSRF-Token: $CSRF" \
        -b /tmp/cookies.txt \
        -d "$data")

    # Check for success
    SUCCESS=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

    if [ "$SUCCESS" = "True" ]; then
        echo "✅ $endpoint - Success"
        # Show first 200 chars of response
        echo "   Response: $(echo "$RESPONSE" | head -c 200)..."
    else
        echo "❌ $endpoint - Failed"
        echo "   Response: $RESPONSE"
    fi
    echo ""
}

# Test each endpoint
echo "=== Testing Individual Endpoints ==="
echo ""

# 1. llm_router_dashboard - Get dashboard data
test_endpoint "llm_router_dashboard" '{}' "success"

# 2. llm_router_models - Get all models
test_endpoint "llm_router_models" '{}' "success"

# 3. llm_router_get_defaults - Get default models
test_endpoint "llm_router_get_defaults" '{}' "success"

# 4. llm_router_discover - Discover models (try ollama)
test_endpoint "llm_router_discover" '{"provider": "ollama"}' "success"

# 5. llm_router_select - Select best model
test_endpoint "llm_router_select" '{"role": "chat", "priority": "quality"}' "success"

# 6. llm_router_fallback - Get fallback chain
test_endpoint "llm_router_fallback" '{"role": "chat"}' "success"

# 7. llm_router_usage - Get usage stats
test_endpoint "llm_router_usage" '{"hours": 24}' "success"

# 8. llm_router_rules - List routing rules
test_endpoint "llm_router_rules" '{"action": "list"}' "success"

# 9. llm_router_set_default - Set default (skip to avoid modifying state)
echo "Skipping llm_router_set_default (would modify state)"
echo ""

# 10. llm_router_auto_configure - Auto configure (skip to avoid modifying state)
echo "Skipping llm_router_auto_configure (would modify state)"
echo ""

echo "=== Test Summary ==="
echo "Tested 8/10 endpoints (2 skipped to avoid state changes)"
echo ""

# Cleanup
rm -f /tmp/cookies.txt
