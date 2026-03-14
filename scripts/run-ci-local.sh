#!/bin/bash
# Local CI Runner for Agent Jumbo
# Uses 'act' to run GitHub Actions locally
#
# Install act:
#   macOS:  brew install act
#   Linux:  curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
#   Windows: choco install act-cli
#
# Usage:
#   ./scripts/run-ci-local.sh          # Run all jobs
#   ./scripts/run-ci-local.sh lint     # Run specific job
#   ./scripts/run-ci-local.sh test     # Run test job
#   ./scripts/run-ci-local.sh --list   # List available jobs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Agent Jumbo Local CI Runner${NC}"
echo "================================"

# Check if act is installed
if ! command -v act &> /dev/null; then
    echo -e "${RED}Error: 'act' is not installed.${NC}"
    echo ""
    echo "Install act:"
    echo "  macOS:   brew install act"
    echo "  Linux:   curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
    echo "  Windows: choco install act-cli"
    echo ""
    echo "Or visit: https://github.com/nektos/act#installation"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running.${NC}"
    echo "Please start Docker and try again."
    exit 1
fi

cd "$PROJECT_ROOT"

# Parse arguments
JOB=""
LIST_JOBS=false
DRY_RUN=false
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --list|-l)
            LIST_JOBS=true
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE="-v"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options] [job_name]"
            echo ""
            echo "Options:"
            echo "  --list, -l      List available jobs"
            echo "  --dry-run, -n   Show what would be run without executing"
            echo "  --verbose, -v   Verbose output"
            echo "  --help, -h      Show this help"
            echo ""
            echo "Jobs:"
            echo "  lint            Run linting and format check"
            echo "  test            Run test suite"
            echo "  test-instruments Run instrument tests"
            echo "  type-check      Run type checking"
            echo "  security        Run security scans"
            echo "  docker-build    Test Docker build"
            echo ""
            echo "Examples:"
            echo "  $0              # Run all jobs"
            echo "  $0 lint         # Run only lint job"
            echo "  $0 test -v      # Run test job with verbose output"
            exit 0
            ;;
        *)
            JOB=$1
            shift
            ;;
    esac
done

# List jobs
if [ "$LIST_JOBS" = true ]; then
    echo -e "${YELLOW}Available jobs:${NC}"
    act -l -W .github/workflows/ci.yml
    exit 0
fi

# Dry run
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Dry run - showing what would be executed:${NC}"
    if [ -n "$JOB" ]; then
        act -n -j "$JOB" -W .github/workflows/ci.yml
    else
        act -n -W .github/workflows/ci.yml
    fi
    exit 0
fi

# Create .actrc if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.actrc" ]; then
    echo -e "${YELLOW}Creating .actrc configuration...${NC}"
    cat > "$PROJECT_ROOT/.actrc" << 'EOF'
# Act configuration for Agent Jumbo
-P ubuntu-latest=catthehacker/ubuntu:act-latest
--container-architecture linux/amd64
EOF
    echo "Created .actrc"
fi

# Run the CI
echo ""
if [ -n "$JOB" ]; then
    echo -e "${GREEN}Running job: $JOB${NC}"
    act -j "$JOB" -W .github/workflows/ci.yml $VERBOSE
else
    echo -e "${GREEN}Running all CI jobs...${NC}"
    act -W .github/workflows/ci.yml $VERBOSE
fi

echo ""
echo -e "${GREEN}✅ CI completed successfully!${NC}"
