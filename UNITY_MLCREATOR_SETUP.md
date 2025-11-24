# Unity ML-Creator with Agent Zero

Complete Docker-based development environment for Unity ML-Agents multiplayer games with AI assistance.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Agent Zero    │────│   Unity MCP      │────│   Unity Editor  │
│   (AI Assistant)│    │   Server         │    │   Containers    │
│                 │    │                  │    │                 │
│ • Code Analysis │    │ • Unity API      │    │ • ML-Agents     │
│ • Docker Mgmt   │    │ • Scene Mgmt     │    │ • Netcode       │
│ • Project Mgmt  │    │ • Asset Import   │    │ • Build Deploy  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────────────┐
                    │  Unity ML-Creator  │
                    │     Project       │
                    │                    │
                    │ • ML-Agents v3+    │
                    │ • Netcode GO       │
                    │ • DOTS (Entities)  │
                    │ • Unity 6000.2.10f1│
                    └────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Windows/macOS/Linux with Docker support
- API keys for LLM providers (OpenAI, Anthropic, or Google)

### One-Command Setup
```bash
# Make setup script executable and run it
chmod +x setup_unity_mlcreator_docker.sh
./setup_unity_mlcreator_docker.sh
```

### Manual Setup
1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Build Custom Agent Zero Image**
   ```bash
   cd docker/run
   docker build -t agent-zero-unity --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .
   cd ../..
   ```

3. **Start Services**
   ```bash
   docker-compose -f docker-compose-fresh.yml up -d
   ```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Unity Project Configuration
UNITY_PROJECT_NAME=UnityMLcreator
UNITY_PROJECT_PATH=/a0/usr/projects/unitymlcreator
UNITY_EDITOR_VERSION=6000.2.10f1

# API Keys (Required)
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Agent Zero Settings
AGENT_PROFILE=developer
AGENT_MEMORY_SUBDIR=mlcreator
AGENT_KNOWLEDGE_SUBDIR=mlcreator
```

### Docker Services

#### Agent Zero (Main AI Assistant)
- **Container**: `agent-zero-fresh`
- **Web UI**: http://localhost:50001
- **SSH Access**: Port 22 (for code execution)
- **Capabilities**:
  - Full Docker command execution
  - Unity project file management
  - ML-Agents training coordination
  - Multiplayer game deployment

#### Unity MCP Server
- **Container**: `mlcreator-unity-mcp`
- **API**: http://localhost:9050
- **Capabilities**:
  - Unity Editor integration
  - Scene and asset management
  - Build pipeline automation
  - ML-Agents environment setup

## 🎯 Key Features

### AI-Powered Development
- **Intelligent Code Analysis**: Agent Zero understands Unity ML-Agents patterns
- **Automated ML Training**: Set up and run ML-Agents training environments
- **Build Optimization**: AI-assisted build configuration and optimization
- **Multiplayer Testing**: Automated testing of Netcode for GameObjects

### Docker Integration
- **Containerized Unity Builds**: Isolated, reproducible builds
- **ML-Agents Training**: GPU-accelerated training in containers
- **Multi-Environment Testing**: Test across different Unity versions
- **Deployment Automation**: Automated deployment pipelines

### Project Management
- **Version Control**: Git integration with Unity projects
- **Dependency Management**: Automated package resolution
- **Asset Organization**: AI-assisted asset categorization
- **Documentation**: Auto-generated project documentation

## 📁 Project Structure

```
UnityMLcreator/
├── .a0proj/                    # Agent Zero project config
│   ├── instructions.md         # Project-specific instructions
│   └── variables.env           # Project variables
├── Assets/
│   ├── Scripts/                # C# game logic
│   ├── ML-Agents/             # ML-Agents configurations
│   ├── Netcode/               # Multiplayer scripts
│   └── Scenes/                # Unity scenes
├── Packages/
│   └── manifest.json          # Unity package dependencies
└── ProjectSettings/           # Unity project settings
```

## 🔄 Workflow Integration

### Development Workflow
1. **Project Setup**: Agent Zero initializes Unity project structure
2. **ML-Agents Configuration**: Sets up training environments and agents
3. **Code Development**: AI-assisted C# development with Unity patterns
4. **Training Pipeline**: Automated ML model training and evaluation
5. **Multiplayer Testing**: Netcode testing and optimization
6. **Build & Deploy**: Automated build and deployment pipelines

### Unity-Specific Instructions
Agent Zero follows these mandatory principles:
1. **ML-First Design**: Design with ML-Agents integration from start
2. **Netcode Architecture**: Implement scalable multiplayer architecture
3. **DOTS Optimization**: Use Entities package for performance
4. **Cross-Platform**: Ensure builds work on target platforms
5. **Version Control**: Proper Git workflow for Unity projects
6. **Documentation**: Maintain comprehensive project docs

## 🛠️ Troubleshooting

### Common Issues

**Agent Zero can't run Docker commands**
```bash
# Check if Docker socket is mounted
docker exec agent-zero-fresh ls -la /var/run/docker.sock

# Verify Docker client is installed
docker exec agent-zero-fresh docker --version
```

**Unity MCP Server not responding**
```bash
# Check Unity MCP logs
docker-compose -f docker-compose-fresh.yml logs unity-mcp-server

# Restart Unity MCP service
docker-compose -f docker-compose-fresh.yml restart unity-mcp-server
```

**Unity project file permissions**
```bash
# Fix permissions if needed
docker exec agent-zero-fresh chown -R agent:agent /a0/usr/projects/unitymlcreator
```

### Logs and Debugging
```bash
# View all service logs
docker-compose -f docker-compose-fresh.yml logs -f

# View specific service logs
docker-compose -f docker-compose-fresh.yml logs agent-zero-fresh

# Access container shell for debugging
docker exec -it agent-zero-fresh /bin/bash
```

## 📊 Monitoring & Metrics

### Health Checks
- Agent Zero Web UI: http://localhost:50001/health
- Unity MCP Server: http://localhost:9050/health

### Resource Usage
```bash
# Monitor container resource usage
docker stats

# Check disk usage
docker system df
```

## 🔐 Security Considerations

- API keys are stored securely in container environment
- Docker socket access is limited to necessary operations
- Unity project files are properly isolated
- Network communication uses internal Docker networks

## 🤝 Contributing

### Adding New Unity Tools
1. Create tool script in `python/tools/`
2. Add Unity-specific logic for ML-Agents/Netcode
3. Update project instructions in `.a0proj/instructions.md`

### Extending MCP Server
1. Modify Unity MCP server configuration
2. Add new Unity API endpoints
3. Update Agent Zero tool integrations

## 📚 Additional Resources

- [Unity ML-Agents Documentation](https://unity-technologies.github.io/ml-agents/)
- [Netcode for GameObjects](https://docs.unity3d.com/Packages/com.unity.netcode@latest)
- [DOTS (Entities)](https://docs.unity3d.com/Packages/com.unity.entities@latest)
- [Agent Zero Documentation](docs/README.md)

## 🎯 Next Steps

1. **Explore Agent Zero**: Visit http://localhost:50001 and start chatting
2. **Load Unity Project**: Ask Agent Zero to analyze your UnityMLcreator project
3. **Setup ML Training**: Configure ML-Agents training environments
4. **Build & Test**: Start developing multiplayer ML-powered games

---

**Happy developing with Unity ML-Creator and Agent Zero! 🚀🎮**
