#!/bin/bash
# Final fix for Gemini model configuration

echo "========================================="
echo "FINAL GEMINI CONFIGURATION FIX"
echo "========================================="

# Update the settings with the correct format for LiteLLM + Google provider
docker exec agent-zero-container sh -c "cat > /tmp/final_settings.py << 'EOF'
import json

# Read current settings
with open('/a0/tmp/settings.json', 'r') as f:
    settings = json.load(f)

# For Google provider with LiteLLM, use gemini/ prefix
settings['chat_model_provider'] = 'google'
settings['chat_model_name'] = 'gemini/gemini-1.5-pro-latest'
settings['chat_model_api_base'] = ''
settings['chat_model_kwargs'] = {}

settings['util_model_provider'] = 'google'
settings['util_model_name'] = 'gemini/gemini-1.5-flash-latest'
settings['util_model_api_base'] = ''
settings['util_model_kwargs'] = {}

settings['browser_model_provider'] = 'google'
settings['browser_model_name'] = 'gemini/gemini-1.5-flash-latest'
settings['browser_model_api_base'] = ''
settings['browser_model_kwargs'] = {}

# For embeddings, use a different model
settings['embed_model_provider'] = 'google'
settings['embed_model_name'] = 'gemini/text-embedding-004'
settings['embed_model_api_base'] = ''
settings['embed_model_kwargs'] = {}

# Write updated settings
with open('/a0/tmp/settings.json', 'w') as f:
    json.dump(settings, f, indent=4)

print('Configuration updated:')
print('- Chat: gemini/gemini-1.5-pro-latest')
print('- Util: gemini/gemini-1.5-flash-latest')
print('- Browser: gemini/gemini-1.5-flash-latest')
print('- Embed: gemini/text-embedding-004')
EOF
python3 /tmp/final_settings.py"

echo ""
echo "Restarting container..."
docker restart agent-zero-container

echo ""
echo "Waiting for server to start..."
sleep 15

echo ""
echo "Verifying configuration..."
docker exec agent-zero-container sh -c "cat /a0/tmp/settings.json | grep model_name | head -5"

echo ""
echo "========================================="
echo "FIX COMPLETE!"
echo "========================================="
echo ""
echo "The correct model names are now set:"
echo "- gemini/gemini-1.5-pro-latest"
echo "- gemini/gemini-1.5-flash-latest"
echo ""

if curl -s http://localhost:50001/health > /dev/null 2>&1; then
    echo "✅ Server is running at http://localhost:50001/"
else
    echo "⚠️ Server is still starting..."
fi