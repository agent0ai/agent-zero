# CI/CD Documentation

## Overview

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipelines for Agent Zero. Our CI/CD system is optimized for speed, reliability, and security with comprehensive caching, parallel execution, and automated security scanning.

## Workflows Overview

| Workflow | Purpose | Frequency | Duration |
|----------|---------|-----------|----------|
| CI | Main integration checks | On push/PR | 10-20 min |
| Lint | Code quality checks | On push/PR | 10-15 min |
| Tests | Comprehensive testing | On push/PR + Nightly | 20-30 min |
| Docker | Image building | On push/PR/Tags + Weekly | 15-25 min |
| Security | Security scanning | On push/PR + Weekly | 30-60 min |

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

The main CI workflow runs on every push and pull request with optimized path filtering and caching. It includes:

- **Lint Job**: Runs Ruff linter and formatter with cache
- **Type Check Job**: Runs MyPy for static type checking with cache
- **Test Job**: Runs pytest on multiple Python versions (3.11, 3.12) with cache
- **Validate Docker Job**: Builds Docker image to ensure it compiles with GitHub Actions cache
- **Requirements Check Job**: Validates dependencies and checks for vulnerabilities

**Triggers**:
- Push to `main`, `development`, or `master` branches (only when code/config changes)
- Pull requests to `main`, `development`, or `master` branches (only when code/config changes)
- Manual trigger via workflow_dispatch
- Nightly builds at 2 AM UTC

**Optimizations**:
- Path filtering: Only runs when `.py`, `requirements*.txt`, config files, or Dockerfile changes
- Caching: Ruff cache, MyPy cache, pytest cache, pip dependencies, Docker layers
- Parallel execution: All jobs run in parallel
- Artifact uploads: Test results uploaded for analysis

**Timeout**: 10-20 minutes per job

### 2. Lint Workflow (`.github/workflows/lint.yml`)

Comprehensive code quality checks with optimized caching:

- **Ruff**: Fast Python linter and formatter with cache
- **Pylint**: Detailed code quality analysis with cache
- **isort**: Import sorting verification with cache
- **Complexity Analysis**: Cyclomatic complexity and maintainability metrics with cache
- **Docstring Coverage**: Documentation coverage checking with cache

**Triggers**:
- Push to `main`, `development`, or `master` branches (only for Python files)
- Pull requests (only for Python files)
- Manual trigger via workflow_dispatch

**Optimizations**:
- Path filtering for efficiency (only runs when Python files or configs change)
- Individual caches for Ruff, Pylint, isort, complexity tools, and docstring tools
- Parallel job execution (all linters run simultaneously)
- Detailed reports with actionable feedback
- Non-blocking warnings for gradual improvement (continue-on-error for non-critical checks)

### 3. Test Workflow (`.github/workflows/test.yml`)

Comprehensive testing suite with optimized caching:

- **Test Suite**: Runs on Ubuntu, Windows, and macOS with pytest cache
- **Code Coverage**: Generates coverage reports with cache
- **Integration Tests**: Runs on main branch pushes and nightly builds
- **Smoke Tests**: Quick validation of core imports

**Matrix Strategy**:
- OS: Ubuntu (3.11, 3.12), Windows (3.12), macOS (3.12)
- Python versions: 3.11, 3.12
- Optimized exclusions to avoid unnecessary combinations

**Optimizations**:
- Path filtering: Only runs when code or test files change
- Caching: Playwright browsers, pytest cache, pip dependencies
- Parallel execution across platforms
- Coverage reports uploaded as artifacts
- JUnit XML test results for GitHub UI integration
- Nightly builds at 3 AM UTC for comprehensive testing

**Triggers**:
- Push to main/development/master (only when code changes)
- Pull requests (only when code changes)
- Nightly schedule at 3 AM UTC
- Manual trigger via workflow_dispatch

### 4. Docker Workflow (`.github/workflows/docker.yml`)

Builds and publishes Docker images with optimized caching:

- Builds on push to `main` and version tags
- Publishes to Docker Hub (not on PRs or scheduled builds)
- Platform: linux/amd64 (Kali base doesn't support arm64)
- Uses shared reusable workflow for consistency

**Triggers**:
- Push to `main` or `master` branch (only when Docker-related files change)
- Version tags (`v*`)
- Pull requests (build only, no push, only when Docker-related files change)
- Weekly schedule on Sundays at 4 AM UTC (catches base image updates)
- Manual trigger via workflow_dispatch

**Optimizations**:
- Path filtering: Only runs when Dockerfile, docker/, requirements, or code changes
- GitHub Actions cache: Docker layer caching (configured in shared workflow)
- BuildKit optimizations: Inline cache enabled
- Weekly builds ensure base image security updates are detected

### 5. Security Workflow (`.github/workflows/security.yml`)

Comprehensive security scanning with multiple tools:

- **CodeQL Analysis**: GitHub's semantic code analysis for Python and JavaScript
- **Semgrep**: Fast static analysis with security, Python, and secrets rulesets
- **Dependency Scan**: pip-audit and Safety for known vulnerabilities
- **Secret Scanning**: truffleHog for leaked credentials
- **License Check**: pip-licenses for compliance verification
- **Summary**: Consolidated status report

**Triggers**:
- Push to main/development/master branches
- Pull requests
- Weekly schedule on Mondays at midnight UTC
- Manual trigger via workflow_dispatch

**Features**:
- Multiple security tools running in parallel
- SARIF results uploaded to GitHub Security tab
- Artifact uploads for detailed analysis
- Continue-on-error for non-blocking security checks
- Comprehensive summary job

**Optimizations**:
- Parallel job execution (all scans run simultaneously)
- Dependency caching for pip packages
- Path ignores for test/docs files to reduce noise
- Results retained for 30 days

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

All workflows use the latest stable versions (verified and tested):
- `actions/checkout@v4` - Repository checkout
- `actions/setup-python@v5` - Python environment setup
- `actions/upload-artifact@v4` - Artifact uploads
- `actions/cache@v4` - Caching for dependencies and tools
- `docker/setup-buildx-action@v3` - Docker BuildKit setup
- `docker/build-push-action@v6` - Docker build and push (Note: v6 exists despite some documentation gaps)
- `github/codeql-action/init@v3` - CodeQL initialization
- `github/codeql-action/analyze@v3` - CodeQL analysis
- `github/codeql-action/upload-sarif@v3` - SARIF upload

## Caching Strategy

Our workflows use comprehensive caching for faster execution:

### Python Dependencies
```yaml
cache: 'pip'
cache-dependency-path: |
  requirements.txt
  requirements.dev.txt
```

### Tool-Specific Caches
- **Ruff**: `~/.cache/ruff`
- **MyPy**: `.mypy_cache`
- **Pylint**: `~/.pylint.d`
- **isort**: `~/.cache/isort`
- **pytest**: `.pytest_cache`
- **Playwright**: `~/.cache/ms-playwright`

### Docker Builds
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

### Cache Benefits
- Reduces workflow execution time by 40-60%
- Speeds up dependency installation
- Accelerates linter and type checker runs
- Prevents unnecessary downloads of Playwright browsers
- Improves Docker build times with layer caching

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

### Permissions
- Minimal permissions (contents: read by default)
- Security-events: write (for security workflow only)
- Packages: write (for Docker workflow only)

### Security Features
- **Dependency Scanning**: pip-audit and Safety for known vulnerabilities
- **Code Analysis**: CodeQL for semantic security analysis
- **SAST**: Semgrep for static application security testing
- **Secret Detection**: truffleHog for credential leaks
- **License Compliance**: pip-licenses for license verification
- **Regular Updates**: Dependabot for dependency updates
- **SARIF Integration**: Security results in GitHub Security tab

### Required Secrets
- `DOCKERHUB_TOKEN` - For Docker Hub publishing
- `SEMGREP_APP_TOKEN` (optional) - For enhanced Semgrep features

### Best Practices
- No secrets in logs (all secrets properly masked)
- Continue-on-error for security scans to avoid blocking development
- Weekly automated security scans
- 30-day retention for security artifacts

## Contributing

When adding new workflows:

1. Follow existing naming conventions
2. Add proper timeouts (10-30 minutes)
3. Use concurrency groups to cancel outdated runs
4. Enable caching for dependencies
5. Add path filtering where appropriate
6. Document new workflows in this file
7. Test thoroughly before merging

## Workflow Execution Times

Typical execution times (with caching):

| Workflow | First Run | Cached Run | Savings |
|----------|-----------|------------|---------|
| CI | 15-20 min | 8-12 min | 40-50% |
| Lint | 12-15 min | 6-9 min | 50% |
| Tests | 25-30 min | 15-20 min | 40% |
| Docker | 20-25 min | 10-15 min | 50% |
| Security | 50-60 min | 30-40 min | 40% |

## Troubleshooting

### Common Issues

#### Cache Miss
**Symptom**: Workflows take longer than usual
**Solution**:
- Check if cache keys have changed
- Verify cache restore keys are correct
- Ensure cache paths exist

#### Workflow Skipped
**Symptom**: Workflow doesn't run on push
**Solution**:
- Check path filters - workflow only runs when relevant files change
- Verify branch names match trigger configuration
- Manual trigger available via workflow_dispatch

#### Security Scan Failures
**Symptom**: Security workflow reports failures
**Solution**:
- Check individual job outputs for specific findings
- Review SARIF results in GitHub Security tab
- Most security checks use continue-on-error, so failures are informational
- Download artifacts for detailed analysis

## Scheduled Workflows

| Time (UTC) | Workflow | Purpose |
|------------|----------|---------|
| 2:00 AM Daily | CI | Nightly integration checks |
| 3:00 AM Daily | Tests | Comprehensive test suite |
| 4:00 AM Sunday | Docker | Weekly base image updates |
| Midnight Monday | Security | Weekly security scan |

## Future Improvements

- [x] Path filtering for efficiency
- [x] Comprehensive caching strategy
- [x] Security scanning workflow
- [x] Nightly builds for CI and tests
- [ ] Add codecov.io integration for coverage tracking
- [ ] Implement automatic version bumping
- [ ] Add release automation
- [ ] Set up staging deployments
- [ ] Add performance benchmarking
- [ ] Implement semantic release
- [ ] Add changelog automation
