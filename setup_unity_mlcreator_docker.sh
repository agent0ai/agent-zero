#!/bin/bash
# Unity ML-Creator Docker Setup Script
# This script sets up Agent Zero with full Docker access for Unity ML-Agents development

set -e

echo "🚀 Setting up Unity ML-Creator Docker Environment"
echo "================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if required directories exist
if [ ! -d "usr/projects/unitymlcreator" ]; then
    echo "📁 Creating Unity project directory..."
    mkdir -p usr/projects/unitymlcreator
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file template..."
    cat > .env << 'EOF'
# Unity ML-Creator Project Configuration
UNITY_PROJECT_NAME=UnityMLcreator
UNITY_PROJECT_PATH=/a0/usr/projects/unitymlcreator
UNITY_EDITOR_VERSION=6000.2.10f1

# API Keys (REQUIRED - Add your actual keys here)
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Docker Configuration
DOCKER_HOST=unix:///var/run/docker.sock
DOCKER_TLS_VERIFY=0

# Agent Zero Configuration
AGENT_PROFILE=developer
AGENT_MEMORY_SUBDIR=mlcreator
AGENT_KNOWLEDGE_SUBDIR=mlcreator

# Unity MCP Server Configuration
MCP_SERVER_PORT=8080
UNITY_MCP_CONTAINER_NAME=mlcreator-unity-mcp
EOF
    echo "⚠️  IMPORTANT: Please edit .env file and add your API keys!"
    echo "   Opening .env file for editing..."
    # Try to open with default editor
    if command -v code >/dev/null 2>&1; then
        code .env
    elif command -v notepad >/dev/null 2>&1; then
        notepad .env
    else
        echo "   Please manually edit .env file with your API keys"
    fi
    read -p "Press Enter after you've added your API keys..."
fi

# Validate that API keys are set (not default values)
if grep -q "your_gemini_api_key_here" .env; then
    echo "❌ Please set your actual API keys in .env file"
    exit 1
fi

echo "🔨 Building Agent Zero with Docker CLI..."
cd docker/run
docker build -t agent-zero-unity --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .
cd ../..

echo "🐳 Starting Unity ML-Creator environment..."
docker-compose -f docker-compose-fresh.yml up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker ps | grep -q agent-zero-fresh; then
    echo "✅ Agent Zero container is running"
else
    echo "❌ Agent Zero container failed to start"
    docker-compose -f docker-compose-fresh.yml logs agent-zero-fresh
    exit 1
fi

if docker ps | grep -q mlcreator-unity-mcp; then
    echo "✅ Unity MCP Server is running"
else
    echo "❌ Unity MCP Server failed to start"
    docker-compose -f docker-compose-fresh.yml logs unity-mcp-server
    exit 1
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo "Agent Zero Web UI: http://localhost:50001"
echo "Unity MCP Server:  http://localhost:9050"
echo ""
echo "📋 Next Steps:"
echo "1. Open http://localhost:50001 in your browser"
echo "2. Configure Agent Zero settings and API keys"
echo "3. Load the UnityMLcreator project in Agent Zero"
echo "4. Start developing with Unity ML-Agents!"
echo ""
echo "🔧 Useful commands:"
echo "• View logs: docker-compose -f docker-compose-fresh.yml logs -f"
echo "• Stop:     docker-compose -f docker-compose-fresh.yml down"
echo "• Restart:  docker-compose -f docker-compose-fresh.yml restart"
echo ""
echo "💡 Agent Zero can now:"
echo "   • Run Docker commands to manage containers"
echo "   • Access and modify the Unity project files"
echo "   • Launch Unity Editor instances in containers"
echo "   • Train ML-Agents models"
echo "   • Deploy multiplayer games with Netcode"
