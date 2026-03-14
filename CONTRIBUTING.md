# Contributing to Agent Jumbo DevOps

Thank you for your interest in contributing to Agent Jumbo DevOps! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and professional. We're building a welcoming community.

## Ways to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Create a new issue with:
   - Clear title describing the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, Kubernetes version if applicable)

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue with:
   - Clear description of the feature
   - Use case and motivation
   - Proposed implementation (optional)

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Follow the development guidelines below
4. Submit a pull request with clear description

## Development Setup

### Prerequisites

- Python 3.10+
- pip and venv
- Git

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/agent-jumbo-deploy/agent-jumbo-devops.git
cd agent-jumbo-devops

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_devops_deploy.py -v

# Run with coverage
pytest tests/ --cov=python/tools/

# Run slow tests only (use --slow flag)
pytest tests/ -m slow
```

### Code Quality

```bash
# Format code
black python/

# Lint code
ruff check python/

# Type checking
mypy python/

# Security check
bandit -r python/
```

## Coding Standards

### Python Style

- Follow PEP 8 (enforced by black and ruff)
- Use type hints for all functions
- Write docstrings for all public functions
- Keep functions focused and testable

### Testing Requirements

- All new code must have corresponding tests
- Minimum 90% code coverage
- Tests must pass: `pytest tests/ -v`
- Use descriptive test names: `test_<function>_<scenario>`

### Commit Messages

Follow conventional commits:

```text
feat: add new deployment strategy
fix: handle edge case in error classification
docs: update deployment guide
test: add integration tests
chore: update dependencies
```

### Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Run full test suite locally
4. Submit PR with clear description
5. Address review feedback
6. Ensure CI/CD passes

## Areas for Contribution

### High Priority

- **SSH Deployment SDK**: Integrate paramiko or fabric
- **AWS Deployment SDK**: Integrate boto3
- **GCP Deployment SDK**: Integrate google-cloud SDK
- **GitHub Actions Integration**: Complete GitHub API integration
- **Canary Deployments**: Advanced deployment strategies
- **WebUI Dashboard**: Real-time deployment monitoring

### Medium Priority

- Performance optimizations
- Additional platform integrations
- Documentation improvements
- Community examples

### Low Priority

- UI/UX enhancements
- Additional monitoring integrations
- Advanced analytics

## Release Process

Maintainers follow semantic versioning (v1.0.0):

1. Create release branch: `release/v1.x.x`
2. Update version numbers
3. Update CHANGELOG
4. Create GitHub release with notes
5. Announce on community channels

## Questions?

- Open an issue for discussions
- Check existing documentation: `/docs/`
- Review API reference: `/docs/DEVOPS_DEPLOYMENT_README.md`

## License

By contributing, you agree your code will be licensed under Apache 2.0.

Thank you for contributing! 🚀
