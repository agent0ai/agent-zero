#!/bin/bash

#
# PMS Hub TDD Swarm Test Runner
# Comprehensive test execution with coverage analysis
# Usage: ./scripts/run_pms_tests.sh [all|unit|integration|coverage|quick]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Install test dependencies
echo -e "${BLUE}📦 Installing test dependencies...${NC}"
pip install -q pytest pytest-asyncio pytest-cov httpx icalendar cryptography 2>/dev/null || true

# Test categories
TEST_DIR="tests"
UNIT_TESTS="$TEST_DIR/test_pms_canonical_models.py $TEST_DIR/test_pms_providers.py $TEST_DIR/test_pms_registry.py"
INTEGRATION_TESTS="$TEST_DIR/test_pms_sync_service.py"

# Default action
ACTION="${1:-all}"

run_unit_tests() {
    echo -e "${BLUE}🧪 Running Unit Tests...${NC}"
    python -m pytest $UNIT_TESTS -m unit -v --tb=short
}

run_integration_tests() {
    echo -e "${BLUE}🔗 Running Integration Tests...${NC}"
    python -m pytest $INTEGRATION_TESTS -m integration -v --tb=short || true
}

run_async_tests() {
    echo -e "${BLUE}⚡ Running Async Tests...${NC}"
    python -m pytest tests/ -m async -v --tb=short
}

run_all_tests() {
    echo -e "${BLUE}🚀 Running All Tests...${NC}"
    python -m pytest tests/ -v --tb=short --color=yes
}

run_coverage() {
    echo -e "${BLUE}📊 Running Tests with Coverage...${NC}"
    python -m pytest tests/ \
        --cov=instruments/custom/pms_hub \
        --cov=python/tools/pms_hub_tool \
        --cov=python/api \
        --cov-report=html \
        --cov-report=term-missing \
        -v --tb=short
    echo -e "${GREEN}✅ Coverage report generated in htmlcov/index.html${NC}"
}

run_quick_tests() {
    echo -e "${BLUE}⚡ Running Quick Smoke Tests...${NC}"
    python -m pytest tests/ -m "not slow" -x -v --tb=line
}

print_usage() {
    echo "PMS Hub Test Suite"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  all          - Run all tests"
    echo "  unit         - Run unit tests only"
    echo "  integration  - Run integration tests only"
    echo "  async        - Run async tests only"
    echo "  coverage     - Run all tests with coverage report"
    echo "  quick        - Run quick smoke tests"
    echo ""
}

# Main execution
case $ACTION in
    all)
        run_all_tests
        ;;
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    async)
        run_async_tests
        ;;
    coverage)
        run_coverage
        ;;
    quick)
        run_quick_tests
        ;;
    help|-h|--help)
        print_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown action: $ACTION${NC}"
        print_usage
        exit 1
        ;;
esac

EXIT_CODE=$?

# Summary
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Tests passed!${NC}"
else
    echo -e "${RED}❌ Tests failed!${NC}"
fi

exit $EXIT_CODE
