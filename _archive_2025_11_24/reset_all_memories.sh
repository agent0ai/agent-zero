#!/bin/bash
# Complete reset of Agent Zero memories and configurations

echo "========================================="
echo "COMPLETE AGENT ZERO RESET"
echo "========================================="

# 1. Stop the container
echo "1. Stopping container..."
docker stop agent-zero-container
echo "   ✅ Container stopped"

# 2. Remove ALL memory files
echo "2. Removing all memory databases..."
docker run --rm -v agent-zero:/data alpine sh -c "
    rm -rf /data/memory/* 2>/dev/null
    rm -rf /data/usr/projects/*/\.a0proj/memory/* 2>/dev/null
    rm -rf /data/tmp/memory/* 2>/dev/null
    echo 'Memory files removed'
"
echo "   ✅ Memory databases cleared"

# 3. Remove all cache and temporary files
echo "3. Clearing all caches..."
docker run --rm -v agent-zero:/data alpine sh -c "
    find /data -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
    find /data -name '*.pyc' -delete 2>/dev/null || true
    find /data -name '*.pyo' -delete 2>/dev/null || true
    rm -rf /data/tmp/chats/* 2>/dev/null || true
    rm -rf /data/.cache/* 2>/dev/null || true
    echo 'Cache cleared'
"
echo "   ✅ All caches cleared"

# 4. Reset Qdrant if it's running
echo "4. Resetting Qdrant collections..."
if docker ps | grep -q qdrant; then
    curl -X DELETE "http://localhost:6333/collections/agent-zero-mlcreator" 2>/dev/null || true
    curl -X DELETE "http://localhost:6333/collections/agent-zero" 2>/dev/null || true
    echo "   ✅ Qdrant collections reset"
else
    echo "   ⚠️ Qdrant not running"
fi

# 5. Create clean settings
echo "5. Creating clean configuration..."
cat > /tmp/clean_settings.json << 'EOF'
{
    "version": "v0.9.7-10",
    "chat_model_provider": "google",
    "chat_model_name": "gemini-1.5-pro",
    "chat_model_api_base": "",
    "chat_model_kwargs": {},
    "chat_model_ctx_length": 128000,
    "chat_model_ctx_history": 0.7,
    "chat_model_vision": true,
    "chat_model_rl_requests": 0,
    "chat_model_rl_input": 0,
    "chat_model_rl_output": 0,
    "util_model_provider": "google",
    "util_model_name": "gemini-1.5-flash",
    "util_model_api_base": "",
    "util_model_ctx_length": 128000,
    "util_model_ctx_input": 0.7,
    "util_model_kwargs": {},
    "util_model_rl_requests": 0,
    "util_model_rl_input": 0,
    "util_model_rl_output": 0,
    "embed_model_provider": "google",
    "embed_model_name": "text-embedding-004",
    "embed_model_api_base": "",
    "embed_model_kwargs": {},
    "embed_model_rl_requests": 0,
    "embed_model_rl_input": 0,
    "browser_model_provider": "google",
    "browser_model_name": "gemini-1.5-flash",
    "browser_model_api_base": "",
    "browser_model_vision": true,
    "browser_model_rl_requests": 0,
    "browser_model_rl_input": 0,
    "browser_model_rl_output": 0,
    "browser_model_kwargs": {},
    "browser_http_headers": {},
    "memory_recall_enabled": true,
    "memory_recall_delayed": false,
    "memory_recall_interval": 3,
    "memory_recall_history_len": 10000,
    "memory_recall_memories_max_search": 12,
    "memory_recall_solutions_max_search": 8,
    "memory_recall_memories_max_result": 5,
    "memory_recall_solutions_max_result": 3,
    "memory_recall_similarity_threshold": 0.7,
    "memory_recall_query_prep": true,
    "memory_recall_post_filter": true,
    "memory_memorize_enabled": true,
    "memory_memorize_consolidation": true,
    "memory_memorize_replace_threshold": 0.9,
    "api_keys": {},
    "auth_login": "",
    "auth_password": "",
    "root_password": "",
    "agent_profile": "agent0",
    "agent_memory_subdir": "mlcreator",
    "agent_knowledge_subdir": "mlcreator",
    "rfc_auto_docker": true,
    "rfc_url": "localhost",
    "rfc_password": "",
    "rfc_port_http": 55080,
    "rfc_port_ssh": 55022,
    "shell_interface": "ssh",
    "stt_model_size": "base",
    "stt_language": "en",
    "stt_silence_threshold": 0.3,
    "stt_silence_duration": 1000,
    "stt_waiting_timeout": 2000,
    "tts_kokoro": true,
    "mcp_servers": "{\n    \"mcpServers\": {}\n}",
    "mcp_client_init_timeout": 10,
    "mcp_client_tool_timeout": 120,
    "mcp_server_enabled": false,
    "mcp_server_token": "vpycry-g7CT6CS2c",
    "a2a_server_enabled": false,
    "variables": "",
    "secrets": "",
    "litellm_global_kwargs": {},
    "update_check_enabled": true
}
EOF

docker cp /tmp/clean_settings.json agent-zero-container:/a0/tmp/settings.json
echo "   ✅ Clean configuration created"

# 6. Start container
echo "6. Starting container with clean state..."
docker start agent-zero-container
sleep 10
echo "   ✅ Container started"

# 7. Verify
echo "7. Verifying configuration..."
docker exec agent-zero-container sh -c "cat /a0/tmp/settings.json | grep -E 'model_name' | head -5"

echo ""
echo "========================================="
echo "RESET COMPLETE!"
echo "========================================="
echo ""
echo "All memories and caches have been cleared."
echo "Configuration has been reset to use:"
echo "- gemini-1.5-pro (chat)"
echo "- gemini-1.5-flash (utility/browser)"
echo "- text-embedding-004 (embeddings)"
echo ""

# Test health
if curl -s http://localhost:50001/health > /dev/null 2>&1; then
    echo "✅ Server is running at http://localhost:50001/"
else
    echo "⚠️ Server is still starting. Please wait..."
fi