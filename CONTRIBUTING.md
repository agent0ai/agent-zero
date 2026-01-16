# Contributing to Agent Zero

Thank you for your interest in contributing to Agent Zero! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/agent-zero.git`
3. Add upstream remote: `git remote add upstream https://github.com/frdel/agent-zero.git`
4. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Docker (optional, for testing Docker builds)
- Git

### Install Development Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements.dev.txt

# Install pre-commit hooks
pre-commit install
```

### Verify Installation

```bash
# Run tests
pytest tests/ -v

# Run linters
ruff check .
ruff format . --check

# Type check
mypy . --ignore-missing-imports
```

## Code Quality

We use multiple tools to maintain code quality:

### Ruff (Linting and Formatting)

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

### MyPy (Type Checking)

```bash
# Run type checker
mypy . --ignore-missing-imports --no-strict-optional
```

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

```bash
# Run hooks manually
pre-commit run --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_fasta2a_client.py -v

# Run with coverage
pytest tests/ --cov=python --cov-report=html

# Run tests in parallel
pytest tests/ -n auto
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix or `_test` suffix
- Use descriptive test names that explain what is being tested
- Follow the Arrange-Act-Assert pattern
- Use fixtures for common setup
- Mock external dependencies

Example:

```python
import pytest
from python.helpers import settings

def test_settings_get_value():
    """Test that settings can retrieve a value."""
    # Arrange
    expected_value = "test"

    # Act
    result = settings.get_settings().get("test_key")

    # Assert
    assert result == expected_value
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow
def test_long_running_operation():
    # Test that takes a long time
    pass

@pytest.mark.integration
def test_external_service():
    # Test that requires external services
    pass
```

Run specific categories:

```bash
# Skip slow tests
pytest tests/ -m "not slow"

# Run only integration tests
pytest tests/ -m integration
```

## Pull Request Process

1. **Update your fork** with latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write clean, readable code
   - Add/update tests
   - Update documentation if needed
   - Follow code style guidelines

4. **Run quality checks**:
   ```bash
   # Run pre-commit hooks
   pre-commit run --all-files

   # Run tests
   pytest tests/ -v

   # Check formatting
   ruff check .
   ruff format . --check
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**:
   - Go to the original repository
   - Click "New Pull Request"
   - Select your feature branch
   - Fill in the PR template
   - Link related issues

8. **Address review feedback**:
   - Make requested changes
   - Push updates to your branch
   - Respond to comments

## Code Style

### Python Style Guidelines

- **Line length**: Maximum 120 characters
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Imports**: Organize with isort (automatic via pre-commit)
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`
  - Private members: `_leading_underscore`

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Detailed description if needed. Can span multiple lines.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
    pass
```

### Comments

- Write self-documenting code when possible
- Use comments to explain **why**, not **what**
- Keep comments up-to-date with code changes
- Remove commented-out code (use git history instead)

## Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples

```bash
# Feature
git commit -m "feat(tools): add new document query tool"

# Bug fix
git commit -m "fix(api): handle missing API key gracefully"

# Documentation
git commit -m "docs: update installation instructions"

# Breaking change
git commit -m "feat(api)!: change authentication method

BREAKING CHANGE: API now requires Bearer token instead of API key"
```

## Project Structure

```
agent-zero/
├── .github/
│   └── workflows/       # CI/CD workflows
├── agents/              # Agent configurations
├── docker/              # Docker configuration
├── docs/                # Documentation
├── instruments/         # Custom instruments
├── python/
│   ├── api/            # API endpoints
│   ├── extensions/     # System extensions
│   ├── helpers/        # Helper utilities
│   └── tools/          # Agent tools
├── tests/              # Test files
├── webui/              # Web UI files
├── agent.py            # Main agent module
├── models.py           # Model configurations
├── run_ui.py           # UI entry point
└── requirements.txt    # Python dependencies
```

## Adding New Features

### 1. Tools

Create a new file in `python/tools/`:

```python
from python.helpers.tool import Tool, Response

class YourTool(Tool):
    async def execute(self, **kwargs):
        # Implementation
        return Response(message="Success")
```

### 2. Extensions

Create a new file in `python/extensions/`:

```python
def initialize(agent):
    # Extension initialization
    pass
```

### 3. API Endpoints

Create a new file in `python/api/`:

```python
from flask import jsonify

def register(app):
    @app.route('/api/your-endpoint', methods=['GET'])
    def your_endpoint():
        return jsonify({"status": "success"})
```

## Need Help?

- Check [Documentation](./docs/README.md)
- Join [Discord](https://discord.gg/B8KZKNsPpj)
- Ask in [GitHub Discussions](https://github.com/frdel/agent-zero/discussions)
- Open an [Issue](https://github.com/frdel/agent-zero/issues)

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
