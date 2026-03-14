#!/bin/bash
set -e

echo "=========================================="
echo "Mahoosuc OS Import Verification"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

verify_step() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        exit 1
    fi
}

# 1. Directory structure
echo "1. Verifying directory structure..."
test -d .claude/commands
verify_step "Commands directory exists"

test -d .claude/agents
verify_step "Agents directory exists"

test -d .claude/skills
verify_step "Skills directory exists"

test -d .claude/hooks
verify_step "Hooks directory exists"

test -d .claude/validation
verify_step "Validation directory exists"

test -d .claude/docs
verify_step "Docs directory exists"

test -d .claude/docs/mahoosuc-reference
verify_step "Mahoosuc reference directory exists"

echo ""

# 2. Content counts
echo "2. Verifying content counts..."

COMMAND_CATEGORIES=$(find .claude/commands -maxdepth 1 -type d -o -name "*.md" | wc -l)
test $COMMAND_CATEGORIES -ge 90
verify_step "Command categories: $COMMAND_CATEGORIES (expected ~95)"

COMMAND_FILES=$(find .claude/commands -name "*.md" | wc -l)
test $COMMAND_FILES -ge 400
verify_step "Command files: $COMMAND_FILES (expected ~414)"

AGENT_FILES=$(find .claude/agents -name "*.md" | wc -l)
test $AGENT_FILES -ge 20
verify_step "Agent files: $AGENT_FILES (expected 21)"

SKILL_DIRS=$(find .claude/skills -maxdepth 1 -type d ! -name skills | wc -l)
test $SKILL_DIRS -ge 5
verify_step "Skill directories: $SKILL_DIRS (expected 5)"

echo ""

# 3. Documentation
echo "3. Verifying documentation..."

test -f .claude/docs/COMMANDS_INDEX.md
verify_step "Commands index exists"

test -f .claude/docs/AGENTS_MIGRATION.md
verify_step "Agents migration guide exists"

test -f .claude/docs/SKILLS_ADAPTATION.md
verify_step "Skills adaptation guide exists"

test -f .claude/docs/HOOKS_REFERENCE.md
verify_step "Hooks reference exists"

test -f .claude/docs/IMPORT_SUMMARY.md
verify_step "Import summary exists"

test -f .claude/docs/USING_MAHOOSUC_COMMANDS.md
verify_step "Usage guide exists"

test -f .claude/docs/AGENT_JUMBO_INTEGRATION.md
verify_step "Integration guide exists"

echo ""

# 4. Test suite
echo "4. Running test suite..."

pytest tests/test_claude_structure.py -v --tb=short
verify_step "Structure tests pass"

pytest tests/test_command_import.py -v --tb=short
verify_step "Command import tests pass"

pytest tests/test_agents_import.py -v --tb=short
verify_step "Agents import tests pass"

pytest tests/test_skills_import.py -v --tb=short
verify_step "Skills import tests pass"

pytest tests/test_hooks_validation_import.py -v --tb=short
verify_step "Hooks/validation tests pass"

pytest tests/test_documentation_import.py -v --tb=short
verify_step "Documentation tests pass"

pytest tests/test_mahoosuc_integration.py -v --tb=short
verify_step "Integration tests pass"

echo ""
echo "=========================================="
echo -e "${GREEN}All verification checks passed!${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Commands: $COMMAND_FILES files across $COMMAND_CATEGORIES categories"
echo "- Agents: $AGENT_FILES agents"
echo "- Skills: $SKILL_DIRS skills"
echo "- Documentation: 7 guides + reference docs"
echo "- Tests: All passing"
echo ""
echo "Next steps:"
echo "1. Review .claude/docs/IMPORT_SUMMARY.md"
echo "2. Explore .claude/docs/USING_MAHOOSUC_COMMANDS.md"
echo "3. Test Claude Code integration (if enabled)"
echo "4. Identify high-value commands for native tool conversion"
