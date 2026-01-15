#!/bin/bash
# Quick health check for Agent Zero setup

echo "🏥 Agent Zero Health Check"
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

# Check Agent Zero
echo "🤖 Agent Zero Service:"
if docker ps --format '{{.Names}}' | grep -q "^agent-zero$"; then
    echo "  ✓ Container: Running"
    
    # Check UI
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:50080 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✓ UI: Accessible at http://localhost:50080"
    else
        echo "  ✗ UI: Not accessible (HTTP $HTTP_CODE)"
    fi
    
    # Check Ollama connectivity from agent-zero
    if docker exec agent-zero curl -s http://ollama:11434/api/tags > /dev/null 2>&1; then
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
if docker volume ls | grep -q "agent_zero_data"; then
    echo "  ✓ Database volume: agent_zero_data"
fi

if [ -d "/home/webemo-aaron/projects/agent-zero/ollama_models/models" ]; then
    SIZE=$(du -sh /home/webemo-aaron/projects/agent-zero/ollama_models 2>/dev/null | cut -f1)
    echo "  ✓ Model directory: $SIZE"
fi
echo ""

# Summary
echo "📊 Summary:"
OLLAMA_OK=$(docker ps --format '{{.Names}}' | grep -q "^ollama$" && echo "yes" || echo "no")
AGENT_OK=$(docker ps --format '{{.Names}}' | grep -q "^agent-zero$" && echo "yes" || echo "no")
UI_OK=$([ "$(curl -s -o /dev/null -w "%{http_code}" http://localhost:50080 2>/dev/null)" = "200" ] && echo "yes" || echo "no")

if [ "$OLLAMA_OK" = "yes" ] && [ "$AGENT_OK" = "yes" ] && [ "$UI_OK" = "yes" ]; then
    echo "  ✅ All systems operational!"
    echo ""
    echo "  🌐 Access Agent Zero: http://localhost:50080"
    echo "  🤖 Model: qwen2.5-coder:7b (local, no API key needed)"
else
    echo "  ⚠️  Some services need attention"
    echo ""
    if [ "$OLLAMA_OK" = "no" ] || [ "$AGENT_OK" = "no" ]; then
        echo "  Fix: cd docker/run && docker-compose up -d"
    fi
fi
