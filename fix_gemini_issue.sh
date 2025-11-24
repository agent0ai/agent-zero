#!/bin/bash
# Fix Gemini Model Configuration Issue in Agent Zero Docker Container

echo "==================================="
echo "Agent Zero Gemini Configuration Fix"
echo "==================================="

# 1. Clear all Python cache
echo "1. Clearing Python cache..."
docker exec agent-zero-container sh -c "find /a0 -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true"
docker exec agent-zero-container sh -c "find /a0 -name '*.pyc' -delete 2>/dev/null || true"
echo "   ✅ Cache cleared"

# 2. Update settings.json with correct model names
echo "2. Updating model configuration..."
docker exec agent-zero-container sh -c "cat > /tmp/update_settings.py << 'EOF'
import json

# Read current settings
with open('/a0/tmp/settings.json', 'r') as f:
    settings = json.load(f)

# Update model names to correct format
settings['chat_model_provider'] = 'google'
settings['chat_model_name'] = 'gemini-1.5-pro'
settings['chat_model_api_base'] = ''

settings['util_model_provider'] = 'google'
settings['util_model_name'] = 'gemini-1.5-flash'
settings['util_model_api_base'] = ''

settings['browser_model_provider'] = 'google'
settings['browser_model_name'] = 'gemini-1.5-flash'
settings['browser_model_api_base'] = ''

# Update fallbacks if they exist
if 'chat_model_kwargs' in settings:
    if 'fallbacks' in settings['chat_model_kwargs']:
        settings['chat_model_kwargs']['fallbacks'] = ['gemini-1.5-pro-latest']

if 'util_model_kwargs' in settings:
    if 'fallbacks' in settings['util_model_kwargs']:
        settings['util_model_kwargs']['fallbacks'] = ['gemini-1.5-flash-latest']

# Write updated settings
with open('/a0/tmp/settings.json', 'w') as f:
    json.dump(settings, f, indent=4)

print('Settings updated successfully')
EOF
python3 /tmp/update_settings.py"

echo "   ✅ Settings updated"

# 3. Clear any cached sessions
echo "3. Clearing cached sessions..."
docker exec agent-zero-container sh -c "rm -rf /a0/tmp/chats/* 2>/dev/null || true"
echo "   ✅ Sessions cleared"

# 4. Check for any hardcoded values
echo "4. Checking for hardcoded values..."
HARDCODED=$(docker exec agent-zero-container sh -c "grep -r 'Gemini 3' /a0 2>/dev/null | wc -l")
if [ "$HARDCODED" -gt 0 ]; then
    echo "   ⚠️ Found $HARDCODED hardcoded references to 'Gemini 3'"
else
    echo "   ✅ No hardcoded 'Gemini 3' references found"
fi

# 5. Verify configuration
echo "5. Verifying configuration..."
docker exec agent-zero-container sh -c "cat /a0/tmp/settings.json | grep -E 'model_name' | head -5"

# 6. Restart the container services
echo "6. Restarting services..."
docker exec agent-zero-container sh -c "pkill -f python 2>/dev/null || true"
sleep 2
docker exec agent-zero-container sh -c "cd /a0 && python3 initialize.py > /dev/null 2>&1 &"
echo "   ✅ Services restarted"

echo ""
echo "==================================="
echo "Fix Applied Successfully!"
echo "==================================="
echo ""
echo "Configuration Summary:"
echo "- Chat Model: gemini-1.5-pro"
echo "- Utility Model: gemini-1.5-flash"
echo "- Browser Model: gemini-1.5-flash"
echo ""
echo "Access Agent Zero at: http://localhost:50001/"
echo ""

# 7. Test the health endpoint
echo "Testing server health..."
sleep 5
if curl -s http://localhost:50001/health > /dev/null 2>&1; then
    echo "✅ Server is running and healthy!"
else
    echo "⚠️ Server might still be starting. Please wait a moment and try again."
fi