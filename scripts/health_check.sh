#!/bin/bash
# Quick health check for Agent Jumbo setup
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_CONTAINER=""
if docker ps --format '{{.Names}}' | grep -q "^agent-jumbo$"; then
    AGENT_CONTAINER="agent-jumbo"
elif docker ps --format '{{.Names}}' | grep -q "^agent-zero$"; then
    AGENT_CONTAINER="agent-zero"
fi

echo "🏥 Agent Jumbo Health Check"
echo "=========================="
echo ""

# Check Ollama
echo "📦 Ollama Service:"
if docker ps --format '{{.Names}}' | grep -q "^ollama$"; then
    STATUS=$(docker inspect ollama --format='{{.State.Health.Status}}' 2>/dev/null || echo "no-health")
    echo "  ✓ Container: Running"
    echo "  Status: $STATUS"

    # Check model
    MODEL=$(docker exec ollama ollama list 2>/dev/null | grep qwen2.5-coder || echo "")
    if [ -n "$MODEL" ]; then
        echo "  ✓ Model: qwen2.5-coder:7b loaded"
    else
        echo "  ✗ Model: Not loaded"
    fi
else
    echo "  ✗ Container: Not running"
fi
echo ""

# Check Agent Jumbo
echo "🤖 Agent Jumbo Service:"
if [ -n "$AGENT_CONTAINER" ]; then
    echo "  ✓ Container: Running"

    # Check UI
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:50080 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✓ UI: Accessible at http://localhost:50080"
    else
        echo "  ✗ UI: Not accessible (HTTP $HTTP_CODE)"
    fi

    # Check Ollama connectivity from agent-jumbo
    if docker exec "$AGENT_CONTAINER" curl -s http://ollama:11434/api/tags > /dev/null 2>&1; then
        echo "  ✓ Ollama Connection: OK"
    else
        echo "  ✗ Ollama Connection: Failed"
    fi
else
    echo "  ✗ Container: Not running"
fi
echo ""

# Check volumes
echo "💾 Data Persistence:"
if docker volume ls | grep -q "agent_jumbo_data"; then
    echo "  ✓ Database volume: agent_jumbo_data"
fi

if [ -d "${ROOT_DIR}/ollama_models/models" ]; then
    SIZE=$(du -sh "${ROOT_DIR}/ollama_models" 2>/dev/null | cut -f1)
    echo "  ✓ Model directory: $SIZE"
fi
echo ""

# Summary
echo "📊 Summary:"
OLLAMA_OK=$(docker ps --format '{{.Names}}' | grep -q "^ollama$" && echo "yes" || echo "no")
AGENT_OK=$([ -n "$AGENT_CONTAINER" ] && echo "yes" || echo "no")
UI_OK=$([ "$(curl -s -o /dev/null -w "%{http_code}" http://localhost:50080 2>/dev/null)" = "200" ] && echo "yes" || echo "no")

if [ "$OLLAMA_OK" = "yes" ] && [ "$AGENT_OK" = "yes" ] && [ "$UI_OK" = "yes" ]; then
    echo "  ✅ All systems operational!"
    echo ""
    echo "  🌐 Access Agent Jumbo: http://localhost:50080"
    echo "  🤖 Model: qwen2.5-coder:7b (local, no API key needed)"
else
    echo "  ⚠️  Some services need attention"
    echo ""
    if [ "$OLLAMA_OK" = "no" ] || [ "$AGENT_OK" = "no" ]; then
        echo "  Fix: cd docker/run && docker-compose up -d"
    fi
fi
