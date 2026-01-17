# Contributing to Agent Zero

Thank you for your interest in contributing to Agent Zero! This document provides guidelines and instructions for contributing.

## 🚀 Quick Start

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/agent-zero.git
   cd agent-zero
   ```

2. **Set up your development environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or .venv\Scripts\activate  # Windows

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements.dev.txt
   playwright install chromium

   # Install pre-commit hooks
   pip install pre-commit
   pre-commit install
   ```

3. **Run the development server**
   ```bash
   python run_ui.py --port=5000
   ```

## 📁 Project Structure

```
agent-zero/
├── agent.py              # Core agent implementation
├── models.py             # LLM model abstraction
├── prompts/              # All agent prompts (edit these to change behavior)
├── python/
│   ├── api/              # REST API endpoints
│   ├── tools/            # Agent tools
│   ├── extensions/       # Lifecycle hooks
│   └── helpers/          # Utility functions
├── instruments/custom/   # Custom instruments
├── agents/               # Agent profiles
├── tests/                # Test suite
└── webui/                # Frontend components
```

## 🔧 Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** following our conventions

3. **Run linting and tests**
   ```bash
   # Lint
   ruff check .
   ruff format .

   # Test
   pytest tests/ -v
   ```

4. **Commit with conventional commits**
   ```
   feat: add new capability
   fix: resolve issue with X
   docs: update documentation
   style: formatting changes
   refactor: restructure code
   test: add tests
   chore: maintenance tasks
   ```

5. **Push and create a Pull Request**

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality:
```bash
pre-commit install
pre-commit run --all-files  # Run manually
```

## 📝 Contribution Types

### Adding Tools

1. Create `python/tools/{tool_name}.py`:
   ```python
   from python.helpers.tool import Tool, Response

   class MyTool(Tool):
       async def execute(self, **kwargs) -> Response:
           result = self.args.get("param")
           return Response(message=result, break_loop=False)
   ```

2. Create prompt `prompts/agent.system.tool.{tool_name}.md`

3. Register in `prompts/agent.system.tools.md`

4. Add tests in `tests/test_{tool_name}.py`

### Adding Extensions

1. Create `python/extensions/{hook_name}/{extension_name}.py`:
   ```python
   from python.helpers.extension import Extension

   class MyExtension(Extension):
       async def execute(self, **kwargs):
           # Hook logic here
           pass
   ```

### Adding Instruments

Use the template: `cp -r instruments/custom/_TEMPLATE instruments/custom/my_instrument`

See `.github/copilot-instructions.md` for detailed instrument guidelines.

### Modifying Prompts

Edit files in `/prompts/`. Key files:
- `agent.system.main.md` - Entry point
- `agent.system.tool.*.md` - Tool definitions
- `fw.*.md` - Framework messages

## ✅ Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_workflow_manager.py

# Run with coverage
pytest --cov=python --cov-report=html

# Run only fast tests
pytest -m "not slow"
```

### Writing Tests

```python
import pytest

class TestMyFeature:
    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test.db")

    def test_basic_operation(self):
        # Test implementation
        assert result['status'] == "success"
```

## 🐳 Local CI with Act

Run GitHub Actions locally:
```bash
# Install act
brew install act  # macOS
# or: https://github.com/nektos/act#installation

# Run CI locally
act -j lint
act -j test
act  # Run all jobs
```

## 📋 Code Style

- **Python**: Follow PEP 8, enforced by Ruff
- **Line length**: 120 characters
- **Type hints**: Recommended for public APIs
- **Docstrings**: Required for public functions/classes
- **Async**: Prefer `async def` for I/O operations

## 🔒 Security

- Never commit API keys or secrets
- Use `.env` for local secrets (not committed)
- Report security issues privately

## 📖 Documentation

- Update relevant docs when changing functionality
- Add docstrings to new functions/classes
- Update `.github/copilot-instructions.md` for architectural changes

## 🤝 Pull Request Guidelines

- Reference related issues
- Include tests for new functionality
- Update documentation as needed
- Keep PRs focused and reasonably sized
- Respond to review feedback promptly

## ❓ Questions?

- Check existing [Issues](https://github.com/agent0ai/agent-zero/issues)
- Join our [Discord](https://discord.gg/B8KZKNsPpj)
- Review [Documentation](./docs/README.md)

Thank you for contributing! 🎉
