#!/bin/bash
# Configure Agent Jumbo to use Ollama with Qwen model

echo "Configuring Agent Jumbo to use Ollama with Qwen2.5-Coder..."

# Update the .env file to add Ollama configuration
cat >> /home/webemo-aaron/projects/agent-jumbo/.env << 'EOF'

# Ollama Configuration (Local LLM)
OLLAMA_API_BASE=http://localhost:11434
EOF

echo "Configuration added to .env file"
echo ""
echo "Now you need to configure the chat model in the Agent Jumbo web UI:"
echo "1. Open http://localhost (or http://192.168.65.3)"
echo "2. Click Settings"
echo "3. Set Chat Model Provider: ollama"
echo "4. Set Chat Model Name: qwen2.5-coder:7b"
echo "5. Set Chat Model API Base: http://localhost:11434"
echo "6. Save settings"
echo ""
echo "Qwen download status:"
ollama list | grep qwen
