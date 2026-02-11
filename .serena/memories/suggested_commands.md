# Suggested Commands

## Running the Application
```bash
# Run the web UI (main entry point)
python run_ui.py

# Run with Docker (local build)
docker build -f DockerfileLocal -t agent-zero-local .
docker run -p 50001:80 agent-zero-local

# Run with Docker (pre-built)
docker pull agent0ai/agent-zero
docker run -p 50001:80 agent0ai/agent-zero
```

## Testing
```bash
# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_websocket_manager.py

# Run with verbose output
pytest -v tests/

# Run async tests (pytest-asyncio is configured)
pytest tests/ -v
```

## Dependencies
```bash
# Install all dependencies (recommended — uses uv)
uv sync

# Install with dev dependencies
uv sync --group dev

# Fallback (pip)
pip install -r requirements.txt
```

## System Utilities (macOS/Darwin)
```bash
# Standard unix tools work on Darwin
git status
git diff
git log --oneline -20
ls -la
grep -r "pattern" directory/
find . -name "*.py"
```

## Environment
- Configuration via `.env` file and `A0_SET_` environment variables
- Settings managed through `python/helpers/settings.py`
- Web UI available at http://localhost:50001 (Docker) or configured port
