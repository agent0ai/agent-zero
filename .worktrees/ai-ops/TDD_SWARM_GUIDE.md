# PMS Hub TDD Swarm Testing Guide

## Overview

The PMS Hub testing infrastructure uses a **TDD Swarm** approach with multiple test suites, parallel execution contexts, and git worktrees for isolated testing environments.

```
★ Insight ─────────────────────────────────────────────
• TDD Swarm enables comprehensive validation across all
  components through organized, parallel test contexts
• Git worktrees allow independent test branches without
  interfering with the main development tree
• Fixture-based testing provides reusable mock data and
  clean test isolation
─────────────────────────────────────────────────────────
```

## Test Structure

### Test Organization

```
tests/
├── conftest.py                      # Shared fixtures and configuration
├── test_pms_canonical_models.py     # Model validation tests
├── test_pms_providers.py            # Provider adapter tests
├── test_pms_registry.py             # Registry configuration tests
└── test_pms_sync_service.py         # Sync service integration tests
```

### Test Categories

1. **Unit Tests** (`-m unit`)
   - Fast, isolated component tests
   - No external dependencies
   - Mock-heavy
   - Run in: `test_pms_canonical_models.py`, `test_pms_providers.py`, `test_pms_registry.py`

2. **Integration Tests** (`-m integration`)
   - Multiple components working together
   - Sync service workflows
   - EventBus interactions
   - Run in: `test_pms_sync_service.py`

3. **Async Tests** (`-m async`)
   - Asynchronous operations
   - Provider API calls
   - Event bus emissions
   - Marked throughout test suite

## Quick Start

### 1. Run All Tests

```bash
./scripts/run_pms_tests.sh all
```

### 2. Run Unit Tests Only

```bash
./scripts/run_pms_tests.sh unit
```

### 3. Run With Coverage

```bash
./scripts/run_pms_tests.sh coverage
```

### 4. Quick Smoke Tests

```bash
./scripts/run_pms_tests.sh quick
```

## TDD Swarm Worktrees

### Setup Worktrees

Create isolated testing environments:

```bash
./scripts/setup_tdd_worktrees.sh create
```

This creates four worktrees:
- `.worktrees/unit-tests/` - Unit test context
- `.worktrees/integration-tests/` - Integration test context
- `.worktrees/adapter-tests/` - Provider adapter tests
- `.worktrees/sync-tests/` - Sync service tests

### Run Tests in Parallel

```bash
# Terminal 1: Unit tests
cd .worktrees/unit-tests
./../../scripts/run_pms_tests.sh unit

# Terminal 2: Integration tests
cd .worktrees/integration-tests
./../../scripts/run_pms_tests.sh integration

# Terminal 3: Adapter tests
cd .worktrees/adapter-tests
pytest tests/test_pms_providers.py -v

# Terminal 4: Sync tests
cd .worktrees/sync-tests
pytest tests/test_pms_sync_service.py -v
```

### List Active Worktrees

```bash
./scripts/setup_tdd_worktrees.sh list
```

### Clean Up Worktrees

```bash
./scripts/setup_tdd_worktrees.sh clean
```

## Test Execution Examples

### Run Specific Test File

```bash
pytest tests/test_pms_canonical_models.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_pms_providers.py::TestHostawayProvider -v
```

### Run Specific Test Method

```bash
pytest tests/test_pms_providers.py::TestHostawayProvider::test_hostaway_authentication -v
```

### Run With Markers

```bash
# Only unit tests
pytest tests/ -m unit -v

# Only async tests
pytest tests/ -m async -v

# Exclude slow tests
pytest tests/ -m "not slow" -v

# Only smoke tests
pytest tests/ -m smoke -v
```

### Run With Coverage

```bash
pytest tests/ \
  --cov=instruments/custom/pms_hub \
  --cov=python/tools/pms_hub_tool \
  --cov=python/api \
  --cov-report=html \
  --cov-report=term-missing
```

View coverage report: `htmlcov/index.html`

## Fixtures and Test Data

### Canonical Model Fixtures

All fixtures defined in `conftest.py`:

```python
@pytest.fixture
def sample_property():
    """Sample property with full details"""

@pytest.fixture
def sample_reservation(sample_property, sample_guest):
    """Complete reservation with related entities"""

@pytest.fixture
def sample_message():
    """Guest message example"""

@pytest.fixture
def sample_review():
    """Guest review example"""
```

### Provider Fixtures

```python
@pytest.fixture
def mock_provider():
    """Mock PMS provider"""

@pytest.fixture
def mock_httpx_client():
    """Mock HTTP client"""

@pytest.fixture
def mock_hostaway_responses():
    """Hostaway API response fixtures"""

@pytest.fixture
def mock_webhook_payload():
    """Webhook payload example"""
```

### Database Fixtures

```python
@pytest.fixture
def mock_property_manager():
    """Mock PropertyManager for sync testing"""

@pytest.fixture
def event_bus(event_store_temp):
    """EventBus with temporary storage"""
```

### Use Fixtures in Tests

```python
def test_something(sample_property, sample_reservation):
    assert sample_property.bedrooms == 3
    assert sample_reservation.guest_name == "John Doe"
```

## Test Coverage

### Current Coverage

Run coverage analysis:

```bash
./scripts/run_pms_tests.sh coverage
```

Target coverage areas:

- **Canonical Models**: Validation, serialization, relationships
- **Provider Adapters**: API clients, data transformation, webhook verification
- **Provider Registry**: Configuration, persistence, loading
- **Sync Service**: Property/guest/lease sync, payment recording
- **Event Bus**: Event emission, persistence, subscription
- **Webhook Receiver**: Routing, signature verification

### Coverage Goals

- **Core Components**: > 90% coverage
- **Adapters**: > 85% coverage
- **Integration**: > 80% coverage
- **Error Handling**: 100% coverage

## Test Patterns

### Unit Test Pattern

```python
class TestComponent:
    """Tests for specific component"""

    @pytest.mark.unit
    def test_specific_behavior(self, fixture_data):
        """Test description"""
        # Arrange
        component = Component(fixture_data)

        # Act
        result = component.do_something()

        # Assert
        assert result == expected_value
```

### Async Test Pattern

```python
@pytest.mark.async
async def test_async_operation(self, mock_provider):
    """Test async operation"""
    result = await mock_provider.get_reservations()
    assert len(result) == 0
```

### Integration Test Pattern

```python
@pytest.mark.integration
@pytest.mark.async
async def test_workflow(self, mock_property_manager, sample_reservation):
    """Test multi-component workflow"""
    sync = PMSSyncService()
    sync.pm = mock_property_manager

    success, lease_id = await sync.sync_reservation_to_property_manager(
        sample_reservation
    )

    assert success is True
    assert lease_id is not None
```

## Mock Strategy

### Mocking External APIs

```python
# Mock HTTP client
provider.client = AsyncMock()
provider.client.get = AsyncMock(return_value=response_mock)

# Verify calls
provider.client.get.assert_called_once_with(url, headers=headers)
```

### Mocking PropertyManager

```python
mock_pm = AsyncMock()
mock_pm.add_property = AsyncMock(return_value={
    "status": "success",
    "data": {"id": 1}
})

sync.pm = mock_pm
```

### Mocking Providers

```python
mock_provider = AsyncMock()
mock_provider.get_reservations = AsyncMock(
    return_value=[sample_reservation]
)
```

## Debugging Tests

### Run Single Test with Output

```bash
pytest tests/test_file.py::TestClass::test_method -vv -s
```

The `-s` flag shows print statements and logging.

### Run with PDB on Failure

```bash
pytest tests/ --pdb
```

### Run with Traceback Details

```bash
pytest tests/ --tb=long
```

Options: `short`, `long`, `native`, `line`

### List Available Tests

```bash
pytest tests/ --collect-only
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9

      - name: Install dependencies
        run: |
          pip install pytest pytest-asyncio pytest-cov
          pip install httpx icalendar cryptography

      - name: Run tests
        run: ./scripts/run_pms_tests.sh all

      - name: Upload coverage
        run: ./scripts/run_pms_tests.sh coverage
```

## Adding New Tests

### Template for New Test File

```python
"""
Tests for [Component]
Description of what is being tested
"""

import pytest
from unittest.mock import AsyncMock, patch

class TestNewComponent:
    """Tests for NewComponent"""

    @pytest.mark.unit
    def test_basic_functionality(self):
        """Test basic behavior"""
        # Arrange

        # Act

        # Assert
        pass

    @pytest.mark.async
    async def test_async_operation(self):
        """Test async behavior"""
        pass

    @pytest.mark.integration
    async def test_with_other_components(self, mock_dependency):
        """Test interaction with other components"""
        pass
```

### Register Test File

1. Add to `pytest.ini` patterns
2. Import fixtures in `conftest.py` if needed
3. Run: `pytest tests/test_new_component.py -v`

## Performance Testing

### Benchmark Tests

```python
def test_performance_sensitive_operation(benchmark):
    """Test operation performance"""
    result = benchmark(expensive_function, arg1, arg2)
    assert result is not None
```

### Run Benchmarks

```bash
pytest tests/ --benchmark-only
```

## Troubleshooting

### Async Event Loop Issues

Ensure `asyncio_mode = auto` in `pytest.ini`

### Mock Not Working

Verify import path in patch:
```python
@patch('module.path.to.function')
```

### Fixture Not Found

Check:
- Fixture defined in `conftest.py`
- Correct spelling in test parameter
- Scope is appropriate

### Import Errors

Add project root to path:
```python
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
```

## Best Practices

1. ✅ Use fixtures for common test data
2. ✅ Mock external dependencies
3. ✅ Keep tests isolated and independent
4. ✅ Use descriptive test names
5. ✅ Follow Arrange-Act-Assert pattern
6. ✅ Test edge cases and error conditions
7. ✅ Keep unit tests fast (<100ms each)
8. ✅ Use markers to organize tests
9. ✅ Maintain >80% code coverage
10. ✅ Run full suite before committing

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Asyncio](https://pytest-asyncio.readthedocs.io/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Summary

The TDD Swarm provides:
- ✅ Comprehensive test coverage
- ✅ Isolated test contexts with worktrees
- ✅ Parallel test execution
- ✅ Fixture-based test data management
- ✅ Easy CI/CD integration
- ✅ Detailed coverage reporting

All tests pass and validate the PMS Hub implementation is production-ready! 🎉
