#!/bin/bash
# Initialize Agent Jumbo with MCP Configuration

echo "🚀 Initializing Agent Jumbo with MCP servers..."
echo ""

# First, let's access the web UI to ensure Agent Jumbo creates its initial settings
echo "📡 Accessing Agent Jumbo web UI to trigger initialization..."
curl -s http://localhost:8080/ > /dev/null 2>&1

echo "⏳ Waiting 3 seconds for initialization..."
sleep 3

# Check if settings file was created
SETTINGS_FILE="/home/webemo-aaron/projects/agent-jumbo/tmp/settings.json"

if [ ! -f "$SETTINGS_FILE" ]; then
    echo "⚠️  Settings file not created yet. Checking in Docker container..."

    # Try to copy from container if it exists there
    docker exec agent-jumbo test -f /a0/tmp/settings.json && \
        docker cp agent-jumbo:/a0/tmp/settings.json "$SETTINGS_FILE" && \
        echo "✅ Copied settings from container" || \
        echo "❌ Settings file not found in container either"
fi

if [ -f "$SETTINGS_FILE" ]; then
    echo "✅ Settings file found: $SETTINGS_FILE"
    echo ""
    echo "Now you can run:"
    echo "  ./setup_mcp.sh"
    echo ""
    echo "to configure MCP servers."
else
    echo ""
    echo "⚠️  Settings file not yet created."
    echo ""
    echo "Please:"
    echo "1. Open http://localhost:8080 in your browser"
    echo "2. Wait for the UI to fully load (you may see a chat interface)"
    echo "3. Then run this script again, or run:"
    echo "   ./setup_mcp.sh"
fi

echo ""
echo "📊 Current Qwen download status:"
tail -2 /tmp/qwen-download.log 2>/dev/null || echo "Download log not found"
