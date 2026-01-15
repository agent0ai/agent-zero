# GitHub Copilot Instructions for Agent Zero

## Project Overview

Agent Zero is a personal, organic agentic framework that grows and learns with you. It's a Python-based AI assistant framework that uses tools, multi-agent cooperation, and extensibility.

## Code Style Guidelines

### Python
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Use async/await for asynchronous operations
- Prefer explicit imports over wildcard imports

### File Organization
- Keep related functionality in the same module
- Use meaningful file and folder names
- Tests should be in the `tests/` directory with `_test.py` suffix

### Dependencies
- Use virtual environments
- Keep `requirements.txt` up to date
- Separate dev dependencies in `requirements.dev.txt`

## Best Practices

### Security
- Never commit secrets or API keys
- Use environment variables for sensitive configuration
- Sanitize user inputs before processing
- Follow principle of least privilege

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Log errors appropriately

### Testing
- Write unit tests for new functionality
- Use pytest for testing
- Mock external dependencies in tests

## Architecture Notes

- `python/tools/` - Contains tool implementations
- `python/helpers/` - Utility functions and helpers
- `python/api/` - API endpoint implementations
- `python/extensions/` - Extension framework
- `prompts/` - System prompts and templates
- `agents/` - Agent configurations
- `instruments/` - Custom instruments

## Common Patterns

### Creating a New Tool
Tools should be placed in `python/tools/` and follow the existing patterns.

### Adding Extensions
Extensions go in `python/extensions/` and use the extensions framework.

### Writing Tests
Tests use pytest and should be placed in `tests/` with descriptive names.
