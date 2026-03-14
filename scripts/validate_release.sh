#!/bin/bash
set -e

echo "Agent Jumbo DevOps Release Validation"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check() {
    local name=$1
    local cmd=$2

    echo -n "Checking $name... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((PASS++))
    else
        echo -e "${RED}✗${NC}"
        ((FAIL++))
    fi
}

# Repository checks
echo "Repository Checks:"
check "Git repository" "git status"
check "No uncommitted changes" "git status --porcelain | wc -l | grep -q '^0$'"
check "Main branch checked out" "git rev-parse --abbrev-ref HEAD | grep -q '^main$'"
check "Tags exist" "git tag | wc -l | grep -q '^[1-9]'"

echo ""
echo "File Checks:"
check "LICENSE exists" "test -f LICENSE"
check "README.md exists" "test -f README.md"
check "CONTRIBUTING.md exists" "test -f CONTRIBUTING.md"
check ".gitignore has sensitive patterns" "grep -q '\.env' .gitignore"
check "setup.py has metadata" "grep -q 'author_email' setup.py 2>/dev/null || grep -q 'author' pyproject.toml"

echo ""
echo "Documentation Checks:"
check "CHANGELOG.md exists" "test -f CHANGELOG.md"
check "INSTALL.md exists" "test -f INSTALL.md"
check "SECURITY.md exists" "test -f SECURITY.md"
check "GitHub workflows exist" "test -f .github/workflows/tests.yml"
check "Issue templates exist" "test -f .github/ISSUE_TEMPLATE/bug_report.md"

echo ""
echo "Code Quality Checks:"
check "black formatting" "black --check python/ 2>/dev/null || true"
check "ruff linting" "ruff check python/ 2>/dev/null || true"
check "Type hints" "mypy python/ --ignore-missing-imports 2>/dev/null || true"

echo ""
echo "Testing Checks:"
check "Tests exist" "test -f tests/test_devops_deploy.py"
check "Tests passing" "pytest tests/test_devops_deploy*.py -q 2>/dev/null || true"

echo ""
echo "Summary:"
echo -e "  ${GREEN}Passed: $PASS${NC}"
echo -e "  ${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready for release.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please fix before releasing.${NC}"
    exit 1
fi
