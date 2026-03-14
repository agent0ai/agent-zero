#!/bin/bash
# Apply MCP Configuration to Agent Jumbo

set -e

echo "🔧 MCP Configuration Setup for Agent Jumbo"
echo "=========================================="
echo ""

# Configuration presets
MINIMAL='{"mcpServers":{"filesystem":{"command":"npx","args":["-y","@modelcontextprotocol/server-filesystem","/home/webemo-aaron/projects"]},"fetch":{"command":"npx","args":["-y","@modelcontextprotocol/server-fetch"]},"sequential-thinking":{"command":"npx","args":["-y","@modelcontextprotocol/server-sequential-thinking"]}}}'

RECOMMENDED='{"mcpServers":{"filesystem":{"command":"npx","args":["-y","@modelcontextprotocol/server-filesystem","/home/webemo-aaron/projects"]},"fetch":{"command":"npx","args":["-y","@modelcontextprotocol/server-fetch"]},"sequential-thinking":{"command":"npx","args":["-y","@modelcontextprotocol/server-sequential-thinking"]},"memory":{"command":"npx","args":["-y","@modelcontextprotocol/server-memory"]},"git":{"command":"npx","args":["-y","@modelcontextprotocol/server-git"]}}}'

# Check if tmp/settings.json exists
SETTINGS_FILE="/home/webemo-aaron/projects/agent-jumbo/tmp/settings.json"

if [ ! -f "$SETTINGS_FILE" ]; then
    echo "❌ Settings file not found: $SETTINGS_FILE"
    echo ""
    echo "Please run Agent Jumbo at least once to create the settings file."
    echo "Access http://localhost:8080 and wait for it to load, then try again."
    exit 1
fi

echo "Select MCP configuration preset:"
echo ""
echo "1) Minimal (filesystem, fetch, sequential-thinking)"
echo "2) Recommended (minimal + memory + git)"
echo "3) Custom (edit mcp_config_claude.json and apply)"
echo "4) View current configuration"
echo "5) Exit"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "📦 Applying MINIMAL configuration..."
        CONFIG="$MINIMAL"
        ;;
    2)
        echo ""
        echo "📦 Applying RECOMMENDED configuration..."
        CONFIG="$RECOMMENDED"
        ;;
    3)
        echo ""
        if [ ! -f "mcp_config_claude.json" ]; then
            echo "❌ mcp_config_claude.json not found"
            exit 1
        fi
        echo "📦 Applying CUSTOM configuration from mcp_config_claude.json..."
        CONFIG=$(cat mcp_config_claude.json | jq -c .)
        ;;
    4)
        echo ""
        echo "📋 Current MCP Configuration:"
        echo "=============================="
        if command -v jq &> /dev/null; then
            cat "$SETTINGS_FILE" | jq '.mcp_servers' 2>/dev/null || echo "No mcp_servers field found"
        else
            grep "mcp_servers" "$SETTINGS_FILE" || echo "No mcp_servers field found"
        fi
        exit 0
        ;;
    5)
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Backup current settings
BACKUP_FILE="${SETTINGS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "💾 Creating backup: $BACKUP_FILE"
cp "$SETTINGS_FILE" "$BACKUP_FILE"

# Update settings file
echo "✏️  Updating settings file..."

# Use jq if available, otherwise use sed (less safe)
if command -v jq &> /dev/null; then
    # Use jq for safe JSON manipulation
    TMP_FILE=$(mktemp)
    cat "$SETTINGS_FILE" | jq --arg mcp "$CONFIG" '.mcp_servers = $mcp' > "$TMP_FILE"
    mv "$TMP_FILE" "$SETTINGS_FILE"
    echo "✅ Configuration updated successfully using jq"
else
    echo "⚠️  jq not found, using sed (less safe)"
    # Escape the JSON for sed
    ESCAPED_CONFIG=$(echo "$CONFIG" | sed 's/[\/&]/\\&/g' | sed 's/"/\\"/g')
    sed -i "s/\"mcp_servers\": *\"[^\"]*\"/\"mcp_servers\": \"$ESCAPED_CONFIG\"/" "$SETTINGS_FILE"
    echo "✅ Configuration updated successfully using sed"
fi

echo ""
echo "🔄 Next steps:"
echo "1. Restart Agent Jumbo container:"
echo "   docker restart agent-jumbo"
echo ""
echo "2. Check logs for MCP initialization:"
echo "   docker logs -f agent-jumbo | grep -i mcp"
echo ""
echo "3. Test in web UI at http://localhost:8080"
echo "   Try: 'List available MCP tools'"
echo ""
echo "4. Verify configuration worked:"
echo "   cat $SETTINGS_FILE | jq '.mcp_servers'"
echo ""
echo "📝 Backup saved to: $BACKUP_FILE"
echo ""

read -p "Restart Agent Jumbo container now? [y/N]: " restart
if [ "$restart" = "y" ] || [ "$restart" = "Y" ]; then
    echo "🔄 Restarting Agent Jumbo..."
    docker restart agent-jumbo
    echo "✅ Container restarted"
    echo ""
    echo "🔍 Watching logs (Ctrl+C to exit)..."
    sleep 2
    docker logs -f agent-jumbo --tail 50
fi
