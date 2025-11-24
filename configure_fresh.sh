#!/bin/bash
# Configure fresh Agent Zero container with correct Gemini settings

echo "========================================="
echo "CONFIGURING FRESH AGENT ZERO"
echo "========================================="

# Create proper configuration
docker exec agent-zero-fresh sh -c "cat > /a0/tmp/settings.json << 'EOF'
{
    \"version\": \"v0.9.7-10\",
    \"chat_model_provider\": \"gemini\",
    \"chat_model_name\": \"gemini-1.5-pro\",
    \"chat_model_api_base\": \"\",
    \"chat_model_kwargs\": {},
    \"chat_model_ctx_length\": 128000,
    \"chat_model_ctx_history\": 0.7,
    \"chat_model_vision\": true,
    \"chat_model_rl_requests\": 0,
    \"chat_model_rl_input\": 0,
    \"chat_model_rl_output\": 0,
    \"util_model_provider\": \"gemini\",
    \"util_model_name\": \"gemini-1.5-flash\",
    \"util_model_api_base\": \"\",
    \"util_model_ctx_length\": 128000,
    \"util_model_ctx_input\": 0.7,
    \"util_model_kwargs\": {},
    \"util_model_rl_requests\": 0,
    \"util_model_rl_input\": 0,
    \"util_model_rl_output\": 0,
    \"embed_model_provider\": \"gemini\",
    \"embed_model_name\": \"text-embedding-004\",
    \"embed_model_api_base\": \"\",
    \"embed_model_kwargs\": {},
    \"embed_model_rl_requests\": 0,
    \"embed_model_rl_input\": 0,
    \"browser_model_provider\": \"gemini\",
    \"browser_model_name\": \"gemini-1.5-flash\",
    \"browser_model_api_base\": \"\",
    \"browser_model_vision\": true,
    \"browser_model_rl_requests\": 0,
    \"browser_model_rl_input\": 0,
    \"browser_model_rl_output\": 0,
    \"browser_model_kwargs\": {},
    \"browser_http_headers\": {},
    \"memory_recall_enabled\": true,
    \"memory_recall_delayed\": false,
    \"memory_recall_interval\": 3,
    \"memory_recall_history_len\": 10000,
    \"memory_recall_memories_max_search\": 12,
    \"memory_recall_solutions_max_search\": 8,
    \"memory_recall_memories_max_result\": 5,
    \"memory_recall_solutions_max_result\": 3,
    \"memory_recall_similarity_threshold\": 0.7,
    \"memory_recall_query_prep\": true,
    \"memory_recall_post_filter\": true,
    \"memory_memorize_enabled\": true,
    \"memory_memorize_consolidation\": true,
    \"memory_memorize_replace_threshold\": 0.9,
    \"api_keys\": {},
    \"auth_login\": \"\",
    \"auth_password\": \"\",
    \"root_password\": \"\",
    \"agent_profile\": \"agent0\",
    \"agent_memory_subdir\": \"default\",
    \"agent_knowledge_subdir\": \"default\",
    \"rfc_auto_docker\": true,
    \"rfc_url\": \"localhost\",
    \"rfc_password\": \"\",
    \"rfc_port_http\": 55080,
    \"rfc_port_ssh\": 55022,
    \"shell_interface\": \"local\",
    \"stt_model_size\": \"base\",
    \"stt_language\": \"en\",
    \"stt_silence_threshold\": 0.3,
    \"stt_silence_duration\": 1000,
    \"stt_waiting_timeout\": 2000,
    \"tts_kokoro\": false,
    \"mcp_servers\": \"{\\n    \\\"mcpServers\\\": {}\\n}\",
    \"mcp_client_init_timeout\": 10,
    \"mcp_client_tool_timeout\": 120,
    \"mcp_server_enabled\": false,
    \"mcp_server_token\": \"vpycry-g7CT6CS2c\",
    \"a2a_server_enabled\": false,
    \"variables\": \"\",
    \"secrets\": \"\",
    \"litellm_global_kwargs\": {},
    \"update_check_enabled\": true
}
EOF"

# Set up .env file in container
docker exec agent-zero-fresh sh -c "cat > /a0/.env << 'EOF'
GEMINI_API_KEY=AIzaSyCi16EEkxxSPcPbhaNSWdd10TC2ipvrLUA
GOOGLE_API_KEY=AIzaSyCi16EEkxxSPcPbhaNSWdd10TC2ipvrLUA
EOF"

echo "Configuration created, restarting container..."
docker restart agent-zero-fresh

echo "Waiting for startup..."
sleep 15

echo ""
echo "========================================="
echo "CONFIGURATION COMPLETE!"
echo "========================================="
echo ""
echo "Fresh container is configured with:"
echo "- Provider: gemini (for all models)"
echo "- Chat: gemini-1.5-pro"
echo "- Utility: gemini-1.5-flash"
echo "- Embeddings: text-embedding-004"
echo ""

if curl -s http://localhost:50001/health > /dev/null 2>&1; then
    echo "✅ Server is running at http://localhost:50001/"
    echo ""
    echo "Opening browser..."
    start http://localhost:50001/
else
    echo "⚠️ Server is still starting, please wait..."
fi