# CI/CD Documentation

## Overview

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipelines for Agent Zero.

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

The main CI workflow runs on every push and pull request. It includes:

- **Lint Job**: Runs Ruff linter and formatter
- **Type Check Job**: Runs MyPy for static type checking
- **Test Job**: Runs pytest on multiple Python versions (3.11, 3.12)
- **Validate Docker Job**: Builds Docker image to ensure it compiles
- **Requirements Check Job**: Validates dependencies and checks for vulnerabilities

**Triggers**:
- Push to `main` or `development` branches
- Pull requests to `main` or `development` branches
- Manual trigger via workflow_dispatch

**Timeout**: 10-20 minutes per job

### 2. Lint Workflow (`.github/workflows/lint.yml`)

Comprehensive code quality checks:

- **Ruff**: Fast Python linter and formatter
- **Pylint**: Detailed code quality analysis
- **isort**: Import sorting verification
- **Complexity Analysis**: Cyclomatic complexity and maintainability metrics
- **Docstring Coverage**: Documentation coverage checking

**Triggers**:
- Push to `main` or `development` branches (only for Python files)
- Pull requests (only for Python files)
- Manual trigger via workflow_dispatch

**Features**:
- Path filtering for efficiency (only runs when Python files change)
- Detailed reports with actionable feedback
- Non-blocking warnings for gradual improvement

### 3. Test Workflow (`.github/workflows/test.yml`)

Comprehensive testing suite:

- **Test Suite**: Runs on Ubuntu, Windows, and macOS
- **Code Coverage**: Generates coverage reports
- **Integration Tests**: Runs on main branch pushes
- **Smoke Tests**: Quick validation of core imports

**Matrix Strategy**:
- OS: Ubuntu (3.11, 3.12), Windows (3.12), macOS (3.12)
- Python versions: 3.11, 3.12

**Features**:
- Parallel execution across platforms
- Coverage reports uploaded as artifacts
- JUnit XML test results for GitHub UI integration
- Playwright browser installation for UI tests

### 4. Docker Workflow (`.github/workflows/docker.yml`)

Builds and publishes Docker images:

- Builds on push to `main` and version tags
- Publishes to Docker Hub
- Platform: linux/amd64 (Kali base doesn't support arm64)

**Triggers**:
- Push to `main` branch
- Version tags (`v*`)
- Pull requests (build only, no push)
- Manual trigger via workflow_dispatch

## Configuration Files

### `ruff.toml`

Ruff linter and formatter configuration:
- Line length: 120
- Target: Python 3.11+
- Enabled rules: pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, flake8-bugbear, flake8-comprehensions
- Excludes vendor files and build artifacts

### `pyproject.toml`

Central Python project configuration:
- pytest settings and markers
- MyPy type checking configuration
- isort and black settings
- Pylint configuration

### `.coveragerc`

Coverage.py configuration:
- Source tracking
- Exclusions for tests and vendor files
- HTML and XML report generation

### `.pre-commit-config.yaml`

Pre-commit hooks for local development:
- Trailing whitespace removal
- YAML/JSON validation
- Ruff linting and formatting
- isort import sorting
- Bandit security checks
- MyPy type checking
- Safety dependency scanning

## Action Versions

All workflows use the latest stable versions:
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/upload-artifact@v4`
- `docker/setup-buildx-action@v3`
- `docker/build-push-action@v6`

## Caching

Python dependencies are cached using:
```yaml
cache: 'pip'
cache-dependency-path: |
  requirements.txt
  requirements.dev.txt
```

Docker builds use GitHub Actions cache:
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

## Local Development

### Setup Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Run Linters Locally

```bash
# Ruff linting
ruff check .

# Ruff formatting
ruff format .

# MyPy type checking
mypy . --ignore-missing-imports

# Pylint
pylint **/*.py
```

### Run Tests Locally

```bash
# Install dev dependencies
pip install -r requirements.dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=python --cov-report=html

# Run specific test file
pytest tests/test_fasta2a_client.py -v
```

### Build Docker Locally

```bash
# Build image
docker build -f DockerfileLocal -t agent-zero:local .

# Run container
docker run -p 50001:80 agent-zero:local
```

## Best Practices

1. **Run tests locally** before pushing:
   ```bash
   pre-commit run --all-files
   pytest tests/ -v
   ```

2. **Keep workflows fast**:
   - Use path filtering for language-specific workflows
   - Enable parallel execution where possible
   - Use caching for dependencies

3. **Use continue-on-error sparingly**:
   - Only for non-critical checks that shouldn't block CI
   - Gradually fix issues to remove continue-on-error

4. **Monitor workflow runs**:
   - Check GitHub Actions tab regularly
   - Fix failing workflows promptly
   - Review security scan results

5. **Update dependencies regularly**:
   - Review Dependabot PRs
   - Test thoroughly before merging
   - Keep action versions up to date

## Troubleshooting

### Workflow Fails on Linting

```bash
# Fix formatting issues
ruff format .

# Fix linting issues automatically
ruff check . --fix

# Check remaining issues
ruff check .
```

### Tests Fail on CI but Pass Locally

- Check Python version (CI uses 3.11 and 3.12)
- Verify all dependencies are in requirements.txt
- Check for platform-specific issues (Windows vs Linux)
- Review test isolation and cleanup

### Docker Build Fails

- Test build locally first
- Check DockerfileLocal syntax
- Verify base image availability
- Review build logs for specific errors

### Pre-commit Hooks Too Slow

```bash
# Run only on changed files
pre-commit run

# Skip specific hooks
SKIP=mypy,pylint pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

## Security

All workflows follow security best practices:

- Minimal permissions (contents: read)
- No secrets in logs
- Dependency scanning with pip-audit
- Code scanning with Bandit
- Regular security updates via Dependabot

## Contributing

When adding new workflows:

1. Follow existing naming conventions
2. Add proper timeouts (10-30 minutes)
3. Use concurrency groups to cancel outdated runs
4. Enable caching for dependencies
5. Add path filtering where appropriate
6. Document new workflows in this file
7. Test thoroughly before merging

## Future Improvements

- [ ] Add codecov.io integration for coverage tracking
- [ ] Implement automatic version bumping
- [ ] Add release automation
- [ ] Set up staging deployments
- [ ] Add performance benchmarking
- [ ] Implement semantic release
- [ ] Add changelog automation
- [ ] Set up nightly builds for integration tests
