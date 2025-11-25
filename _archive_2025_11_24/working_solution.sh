#!/bin/bash
# Working solution without modifying core code

echo "========================================="
echo "WORKING CONFIGURATION SOLUTION"
echo "========================================="

# The trick is to use the model names that work with the current code structure
docker exec agent-zero-container sh -c "cat > /tmp/working_config.py << 'EOF'
import json

with open('/a0/tmp/settings.json', 'r') as f:
    settings = json.load(f)

# For Google provider, the code adds 'google/' prefix automatically
# So we need to provide names WITHOUT any prefix for it to work correctly

# Chat models - use the format that LiteLLM expects after 'google/' is added
# 'google/' + 'gemini-1.5-pro-latest' = 'google/gemini-1.5-pro-latest'
settings['chat_model_provider'] = 'gemini'  # Use 'gemini' provider instead
settings['chat_model_name'] = 'gemini-1.5-pro-latest'
settings['chat_model_api_base'] = ''

settings['util_model_provider'] = 'gemini'  # Use 'gemini' provider instead
settings['util_model_name'] = 'gemini-1.5-flash-latest'
settings['util_model_api_base'] = ''

settings['browser_model_provider'] = 'gemini'
settings['browser_model_name'] = 'gemini-1.5-flash-latest'
settings['browser_model_api_base'] = ''

# For embeddings, use text-embedding-004
settings['embed_model_provider'] = 'google'
settings['embed_model_name'] = 'text-embedding-004'
settings['embed_model_api_base'] = ''

with open('/a0/tmp/settings.json', 'w') as f:
    json.dump(settings, f, indent=4)

print('Configuration updated:')
print('Chat: gemini/gemini-1.5-pro-latest')
print('Util: gemini/gemini-1.5-flash-latest')
print('Embed: google/text-embedding-004')
print('')
print('Using gemini provider for chat/util models to avoid double prefix')
EOF
python3 /tmp/working_config.py"

echo ""
echo "Restarting container..."
docker restart agent-zero-container

echo ""
echo "Waiting for server..."
sleep 15

echo ""
echo "Verifying configuration..."
docker exec agent-zero-container sh -c "cat /a0/tmp/settings.json | grep -E 'model_provider|model_name' | head -8"

echo ""
echo "========================================="
echo "SOLUTION APPLIED!"
echo "========================================="
echo ""
echo "The configuration now uses:"
echo "- 'gemini' provider for chat/util models (avoids double prefix)"
echo "- 'google' provider for embeddings"
echo ""

if curl -s http://localhost:50001/health > /dev/null 2>&1; then
    echo "✅ Server is running at http://localhost:50001/"
else
    echo "⚠️ Server is starting..."
fi