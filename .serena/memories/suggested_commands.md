# Agent Zero Development Commands

## Installation and Setup

### Initial Setup
```bash
# Clone repository
git clone https://github.com/agent0ai/agent-zero
cd agent-zero

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Copy environment template
cp example.env .env
# Edit .env with your API keys and configuration
```

### Docker Setup (Recommended)
```bash
# Build and run Docker container
docker-compose up

# Or run with Docker directly
docker run -p 5000:5000 agent-zero
```

## Running Agent Zero

### Web UI Mode
```bash
# Default (port 5000)
python run_ui.py

# Custom port
python run_ui.py --port=5555

# Or set in .env: WEB_UI_PORT=5555
```

### CLI Mode
```bash
python run_cli.py
```

### Development Mode (VS Code)
```
1. Open VS Code/Cursor/Windsurf
2. Go to Debug panel
3. Select "run_ui.py" configuration
4. Press F5 or click green play button
```

## Development Commands

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/rate_limiter_test.py

# Run with coverage
python -m pytest --cov=python tests/
```

### Code Quality
```bash
# Type checking (if configured)
mypy python/

# Format checking (if configured)
black --check python/
flake8 python/
```

### Dependencies Management
```bash
# Update requirements
pip freeze > requirements.txt

# Update specific requirement files
python update_reqs.py

# Install development dependencies
pip install -r requirements.dev.txt
```

## Docker Commands

### Container Management
```bash
# View running containers
docker ps

# Access container shell
docker exec -it agent-zero /bin/bash

# View logs
docker logs agent-zero

# Stop container
docker stop agent-zero

# Remove container
docker rm agent-zero
```

## Git Commands

### Common Operations
```bash
# Check status
git status

# Create feature branch
git checkout -b feature/your-feature

# Stage changes
git add .

# Commit with message
git commit -m "Description of changes"

# Push to remote
git push origin feature/your-feature

# Update from main
git pull origin main
```

## Utility Commands (Windows)

### File Operations
```bash
# List files
dir
# or
ls (if using PowerShell/Git Bash)

# Change directory
cd path\\to\\directory

# Create directory
mkdir new_directory

# Remove file
del filename
# or
rm filename (PowerShell/Git Bash)

# Copy file
copy source destination
# or
cp source destination (PowerShell/Git Bash)
```

### Process Management
```bash
# View running processes
tasklist

# Kill process
taskkill /PID process_id /F

# Check Python version
python --version

# Check pip packages
pip list
```

## Environment Variables

Key variables to set in `.env`:
- `API_KEY_*`: Your LLM provider API keys
- `CHAT_MODEL_*`: Chat model configuration
- `UTIL_MODEL_*`: Utility model configuration
- `WEB_UI_PORT`: Web UI port (default 5000)
- `TOKENIZER_*`: Tokenizer settings
- `MEMORY_*`: Memory configuration
- `KNOWLEDGE_*`: Knowledge base settings

## Debugging Tips

### VS Code Debugging
- Set breakpoints by clicking left of line numbers
- Use Debug Console for runtime inspection
- Check Variables panel for current state
- Use Call Stack to trace execution

### Common Issues
```bash
# Port already in use
# Change port in .env or use --port flag

# Missing dependencies
pip install -r requirements.txt

# Docker issues
docker system prune  # Clean up Docker
docker-compose down  # Stop all services
docker-compose up --build  # Rebuild containers

# Permission issues (Windows)
# Run terminal/IDE as Administrator
```

## MCP Server Commands

### Starting MCP Servers
```bash
# FastMCP server (if configured)
python -m fastmcp

# Custom MCP server
python python/helpers/mcp_server.py
```

## Project Management

### Creating New Tools
1. Create new file in `python/tools/`
2. Inherit from Tool base class
3. Implement execute method
4. Tool auto-discovered at runtime

### Creating New Prompts
1. Add markdown file to `prompts/`
2. Use template variables as needed
3. Reference in agent configuration

### Working with Projects
- Each project has isolated workspace
- Located in project-specific directories
- Switch projects via UI or configuration